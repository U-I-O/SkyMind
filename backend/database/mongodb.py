import motor.motor_asyncio
from beanie import init_beanie
from config.settings import settings
from config.logging_config import get_logger
from .models import (
    User, Drone, Event, Task, NoFlyZone, UserRole, 
    DetectionConfig, VideoSource, AgentLog, AgentState, DroneStatus, GeoPoint,
    TaskType, TaskStatus, Location
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
    """创建初始数据，如默认管理员用户、示例无人机等"""
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
        
        # 检查是否已有无人机数据
        drone_count = await Drone.count()
        if drone_count == 0:
            logger.info("数据库中无无人机数据，开始创建12个示例无人机...")
            sample_drones = []
            base_lat, base_lon = 30.54, 114.36 # 武汉大学附近基准点
            for i in range(1, 13):
                lat = base_lat + (i - 6) * 0.001
                lon = base_lon + (i % 3 - 1) * 0.001
                status_options = [DroneStatus.IDLE, DroneStatus.FLYING, DroneStatus.CHARGING, DroneStatus.MAINTENANCE, DroneStatus.OFFLINE]
                drone = Drone(
                    name=f"示例无人机 {i}",
                    model=f"SkyMind-M{i % 4 + 1}",
                    status=status_options[i % len(status_options)],
                    battery_level=float(100 - i * 5),
                    current_location=GeoPoint(
                        coordinates=[lon, lat],
                        altitude=float(50 + i * 10)
                    ),
                    max_flight_time=float(30 + i % 5),
                    max_speed=float(15 + i % 3),
                    max_altitude=float(500 + i * 10),
                    camera_equipped=bool(i % 2 == 0),
                    payload_capacity=float(i % 3)
                )
                sample_drones.append(drone)
            
            await Drone.insert_many(sample_drones)
            logger.info(f"成功创建了 {len(sample_drones)} 个示例无人机")
        
        # 检查是否已有任务数据
        task_count = await Task.count()
        if task_count == 0:
            logger.info("数据库中无任务数据，开始创建示例任务...")
            
            # 获取一些无人机ID用于关联
            drones = await Drone.find().limit(4).to_list()
            drone_ids = [drone.drone_id for drone in drones]
            
            # 创建示例任务
            sample_tasks = [
                Task(
                    title="市中心建筑巡检",
                    description="对市中心重要建筑进行例行无人机巡检",
                    type=TaskType.INSPECTION,
                    priority=3,
                    status=TaskStatus.IN_PROGRESS,
                    created_by="admin",
                    assigned_drones=[drone_ids[0]] if drone_ids else [],
                    start_location=Location(
                        position=GeoPoint(
                            coordinates=[114.35, 30.52],
                            altitude=100.0
                        ),
                        name="武汉市中心"
                    ),
                    end_location=Location(
                        position=GeoPoint(
                            coordinates=[114.36, 30.53],
                            altitude=100.0
                        ),
                        name="武汉市政府"
                    )
                ),
                Task(
                    title="紧急物资运送",
                    description="向东湖高新区运送医疗物资",
                    type=TaskType.DELIVERY,
                    priority=8,
                    status=TaskStatus.IN_PROGRESS,
                    created_by="admin",
                    assigned_drones=[drone_ids[1]] if len(drone_ids) > 1 else [],
                    start_location=Location(
                        position=GeoPoint(
                            coordinates=[114.37, 30.51],
                            altitude=50.0
                        ),
                        name="中心医院"
                    ),
                    end_location=Location(
                        position=GeoPoint(
                            coordinates=[114.41, 30.50],
                            altitude=50.0
                        ),
                        name="东湖高新区"
                    )
                ),
                Task(
                    title="环境监测任务",
                    description="对长江沿岸进行环境质量监测",
                    type=TaskType.INSPECTION,
                    priority=4,
                    status=TaskStatus.COMPLETED,
                    created_by="admin",
                    assigned_drones=[drone_ids[2]] if len(drone_ids) > 2 else [],
                    start_location=Location(
                        position=GeoPoint(
                            coordinates=[114.28, 30.58],
                            altitude=80.0
                        ),
                        name="长江大桥"
                    ),
                    end_location=Location(
                        position=GeoPoint(
                            coordinates=[114.32, 30.60],
                            altitude=80.0
                        ),
                        name="长江沿岸"
                    )
                ),
                Task(
                    title="城市安防巡逻",
                    description="对主要交通干道进行安全巡逻",
                    type=TaskType.SURVEILLANCE,
                    priority=6,
                    status=TaskStatus.COMPLETED,
                    created_by="admin",
                    assigned_drones=[drone_ids[3]] if len(drone_ids) > 3 else [],
                    start_location=Location(
                        position=GeoPoint(
                            coordinates=[114.39, 30.55],
                            altitude=120.0
                        ),
                        name="武汉火车站"
                    ),
                    end_location=Location(
                        position=GeoPoint(
                            coordinates=[114.39, 30.49],
                            altitude=120.0
                        ),
                        name="武昌火车站"
                    )
                )
            ]
            
            # 保存示例任务
            for task in sample_tasks:
                await task.insert()
            
            logger.info(f"成功创建了 {len(sample_tasks)} 个示例任务")
            
            # 为分配了任务的无人机更新assigned_tasks字段
            for i, drone_id in enumerate(drone_ids):
                if i < len(sample_tasks):
                    drone = await Drone.find_one({"drone_id": drone_id})
                    if drone:
                        drone.assigned_tasks.append(sample_tasks[i].task_id)
                        await drone.save()
        
    except Exception as e:
        logger.error(f"创建初始数据失败: {str(e)}")
        # 不抛出异常，允许服务继续启动

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