import motor.motor_asyncio
from beanie import init_beanie
from config.settings import settings
from config.logging_config import get_logger
from .models import (
    User, Drone, Event, Task, NoFlyZone, UserRole, 
    DetectionConfig, VideoSource, AgentLog, AgentState
)

logger = get_logger("database")

async def init_db():
    """初始化数据库连接和Beanie ORM"""
    try:
        logger.info(f"正在连接到MongoDB: {settings.MONGODB_URL}")
        
        # 创建Motor客户端
        client = motor.motor_asyncio.AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        
        # 检查是否可以连接
        await client.server_info()
        logger.info("MongoDB连接成功")
        
        # 初始化Beanie ORM
        db = client[settings.DATABASE_NAME]
        
        document_models = [
            User, Drone, Event, Task, NoFlyZone, 
            DetectionConfig, VideoSource, AgentLog, AgentState
        ]
        
        await init_beanie(
            database=db,
            document_models=document_models
        )
        
        logger.info(f"Beanie ORM初始化成功，数据库: {settings.DATABASE_NAME}")
        
        # 创建索引
        for model in document_models:
            logger.debug(f"为模型 {model.__name__} 创建索引")
        
        # 返回数据库实例
        return db
    
    except Exception as e:
        logger.error(f"MongoDB连接失败: {str(e)}")
        raise

async def create_initial_data():
    """创建初始数据"""
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    try:
        # 检查是否已有管理员用户
        admin_exists = await User.find_one({"role": "admin"})
        
        if not admin_exists:
            # 创建默认管理员用户
            admin_user = User(
                username="admin",
                email="admin@skymind.ai",
                hashed_password=pwd_context.hash("adminpassword"),
                full_name="系统管理员",
                role=UserRole.ADMIN
            )
            await admin_user.insert()
            logger.info("创建了默认管理员用户")
        
        # 可以在这里添加其他初始数据的创建
        
    except Exception as e:
        logger.error(f"创建初始数据失败: {str(e)}")
        raise

# 数据库会话上下文管理器
class DatabaseSession:
    """数据库会话上下文管理器，用于事务管理"""
    def __init__(self, client=None):
        self.client = client
        self.session = None
    
    async def __aenter__(self):
        if not self.client:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
        self.session = await self.client.start_session()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.end_session()

# 查询和操作助手函数
async def get_document_by_id(model, doc_id, field_name="id"):
    """通用的根据ID获取文档的函数"""
    query = {field_name: doc_id}
    return await model.find_one(query)

async def list_documents(model, filter_dict=None, skip=0, limit=100, sort_field=None, sort_order=1):
    """通用的列出文档的函数"""
    if filter_dict is None:
        filter_dict = {}
    
    query = model.find(filter_dict).skip(skip).limit(limit)
    
    if sort_field:
        query = query.sort(sort_field, sort_order)
    
    return await query.to_list()