
export const defaultEvents = [
  {
    id: 'event-001',
    title: '异常入侵警报',
    description: '东湖周边区域检测到未授权人员入侵',
    severity: 'high',
    timestamp: '2025-04-18 00:12:53',
    location: '东湖安防区 A-3 区域',
    coordinates: [114.367, 30.541] 
  },
  {
    id: 'event-002',
    title: '车辆异常停留',
    description: '检测到可疑车辆在南门停留超过30分钟',
    severity: 'medium',
    timestamp: '2025-04-17 23:42:53',
    location: '南门停车场',
    coordinates: [114.358, 30.534]
  },
  {
    id: 'event-003',
    title: '围栏振动告警',
    description: '西北角围栏检测到多次振动信号',
    severity: 'medium',
    timestamp: '2025-04-17 22:18:35',
    location: '西北角围栏',
    coordinates: [114.351, 30.548]
  },
  {
    id: 'event-004',
    title: '巡逻无人机离线',
    description: 'Drone-5368 在巡逻过程中意外离线',
    severity: 'low',
    timestamp: '2025-04-17 19:25:12',
    location: '东湖研究区',
    coordinates: [114.372, 30.545]
  },
  {
    id: 'event-005',
    title: '设备异常',
    description: '摄像头 CAM-2374 视频信号丢失',
    severity: 'low',
    timestamp: '2025-04-17 16:43:31',
    location: '主教学楼',
    coordinates: [114.360, 30.537]
  }
];