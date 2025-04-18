from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from config.settings import settings
from database.models import User, UserRole
from config.logging_config import get_logger

# 添加日志记录器
logger = get_logger("auth.security")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """获取当前用户"""
    logger.info(f"验证token: {token[:20]}...")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 解码令牌
        # logger.info(f"开始解码token，使用密钥: {settings.SECRET_KEY[:5]}...")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # logger.info(f"Token解码成功，payload: {payload}")
        
        username: str = payload.get("sub")
        
        if username is None:
            logger.error("Token中缺少用户名(sub)")
            raise credentials_exception
        
        token_data = TokenData(username=username, role=payload.get("role"))
        # logger.info(f"解析token数据: username={token_data.username}, role={token_data.role}")
        
    except JWTError as e:
        logger.error(f"JWT解码错误: {str(e)}")
        raise credentials_exception
    
    # 从数据库获取用户
    # logger.info(f"从数据库查询用户: {token_data.username}")
    user = await User.find_one({"username": token_data.username})
    if user is None:
        logger.error(f"用户不存在: {token_data.username}")
        raise credentials_exception
    
    logger.info(f"用户认证成功: {user.username}, 角色: {user.role}")
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        logger.warning(f"用户已禁用: {current_user.username}")
        raise HTTPException(status_code=400, detail="用户已禁用")
    return current_user

def check_admin_permission(current_user: User = Depends(get_current_active_user)) -> User:
    """检查管理员权限"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    return current_user

def check_manager_permission(current_user: User = Depends(get_current_active_user)) -> User:
    """检查管理员或经理权限"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员或经理权限"
        )
    return current_user

def check_operator_permission(current_user: User = Depends(get_current_active_user)) -> User:
    """检查操作员或更高权限"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.OPERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要操作员或更高权限"
        )
    return current_user