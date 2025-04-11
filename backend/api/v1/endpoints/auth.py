from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel

from config.logging_config import get_logger
from config.settings import settings
from database.models import User, UserRole
from core.security import create_access_token, get_current_user, get_current_active_user

logger = get_logger("api.auth")

router = APIRouter()

# 认证相关模型
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.VIEWER

class UserOut(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    role: UserRole
    is_active: bool
    last_login: Optional[datetime] = None

class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

# 密码处理上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 登录接口
@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await User.find_one({"username": form_data.username})
    
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已被禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    await user.save()
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    logger.info(f"用户 {user.username} 登录成功")
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# 注册新用户
@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, current_user: User = Depends(get_current_active_user)):
    # 只有管理员可以创建新用户
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    # 检查用户名是否已存在
    existing_user = await User.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    existing_email = await User.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在"
        )
    
    # 创建新用户
    hashed_password = pwd_context.hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role
    )
    
    await new_user.insert()
    
    logger.info(f"管理员 {current_user.username} 创建了新用户 {new_user.username}")
    
    return UserOut(
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        is_active=new_user.is_active,
        last_login=new_user.last_login
    )

# 获取当前用户信息
@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# 更新用户信息
@router.put("/users/{username}", response_model=UserOut)
async def update_user(
    username: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    # 只有管理员或用户本人可以更新信息
    if current_user.role != UserRole.ADMIN and current_user.username != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    # 获取要更新的用户
    user = await User.find_one({"username": username})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 如果不是管理员，限制可以更新的字段
    if current_user.role != UserRole.ADMIN:
        if user_update.role is not None or user_update.is_active is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足，无法更新角色或激活状态"
            )
    
    # 更新字段
    if user_update.email is not None:
        # 检查邮箱是否已被其他用户使用
        existing_email = await User.find_one({"email": user_update.email, "username": {"$ne": username}})
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被其他用户使用"
            )
        user.email = user_update.email
    
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    
    if user_update.role is not None and current_user.role == UserRole.ADMIN:
        user.role = user_update.role
    
    if user_update.is_active is not None and current_user.role == UserRole.ADMIN:
        user.is_active = user_update.is_active
    
    if user_update.password is not None:
        user.hashed_password = pwd_context.hash(user_update.password)
    
    await user.save()
    
    logger.info(f"用户 {username} 信息已更新")
    
    return UserOut(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        last_login=user.last_login
    )

# 获取所有用户（仅管理员）
@router.get("/users", response_model=List[UserOut])
async def get_users(current_user: User = Depends(get_current_active_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    users = await User.find_all().to_list()
    
    return [
        UserOut(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            last_login=user.last_login
        )
        for user in users
    ]

# 删除用户（仅管理员）
@router.delete("/users/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    username: str,
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    # 防止删除自己
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除当前登录的用户"
        )
    
    # 获取用户
    user = await User.find_one({"username": username})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 删除用户
    await user.delete()
    
    logger.info(f"管理员 {current_user.username} 删除了用户 {username}")