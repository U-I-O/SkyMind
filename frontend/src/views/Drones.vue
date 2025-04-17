<template>
  <div class="h-full">
    <!-- 使用全局地图，不需要在此页面添加地图组件 -->
    <div class="p-4 h-full overflow-hidden">
      <div class="h-full grid grid-cols-12 gap-4">
        <!-- 左侧面板 -->
        <div class="col-span-3 flex flex-col gap-4 pointer-events-auto h-full overflow-hidden">
          <!-- 标题和操作按钮 -->
          <div class="floating-card bg-white bg-opacity-95">
            <div class="flex justify-between items-center mb-4">
              <h1 class="text-2xl font-bold">无人机管理</h1>
              
              <!-- 操作按钮 -->
              <div class="flex space-x-3">
                <n-button type="primary" @click="showAddDroneModal = true">
                  <template #icon>
                    <n-icon><plus-icon /></n-icon>
                  </template>
                  添加无人机
                </n-button>
                
                <n-button @click="refreshData">
                  <template #icon>
                    <n-icon><reload-icon /></n-icon>
                  </template>
                  刷新
                </n-button>
              </div>
            </div>
          </div>
          
          <!-- 无人机状态统计 (独立面板) -->
          <div class="floating-card bg-white bg-opacity-95">
            <h2 class="font-bold text-lg mb-4">无人机状态</h2>
            <div class="grid grid-cols-5 gap-4">
              <div class="flex flex-col items-center">
                <div class="w-12 h-12 rounded-full flex items-center justify-center bg-blue-100 text-blue-500 mb-2">
                  <n-icon size="24"><drone-icon /></n-icon>
                </div>
                <div class="text-sm text-gray-500">总无人机</div>
                <div class="text-xl font-bold">{{ droneStats.total }}</div>
              </div>
              
              <div class="flex flex-col items-center">
                <div class="w-12 h-12 rounded-full flex items-center justify-center bg-green-100 text-green-500 mb-2">
                  <n-icon size="24"><check-icon /></n-icon>
                </div>
                <div class="text-sm text-gray-500">在线</div>
                <div class="text-xl font-bold">{{ droneStats.online }}</div>
              </div>
              
              <div class="flex flex-col items-center">
                <div class="w-12 h-12 rounded-full flex items-center justify-center bg-yellow-100 text-yellow-500 mb-2">
                  <n-icon size="24"><flight-icon /></n-icon>
                </div>
                <div class="text-sm text-gray-500">飞行中</div>
                <div class="text-xl font-bold">{{ droneStats.flying }}</div>
              </div>
              
              <div class="flex flex-col items-center">
                <div class="w-12 h-12 rounded-full flex items-center justify-center bg-purple-100 text-purple-500 mb-2">
                  <n-icon size="24"><thunderbolt-icon /></n-icon>
                </div>
                <div class="text-sm text-gray-500">充电中</div>
                <div class="text-xl font-bold">{{ droneStats.charging }}</div>
              </div>
              
              <div class="flex flex-col items-center">
                <div class="w-12 h-12 rounded-full flex items-center justify-center bg-red-100 text-red-500 mb-2">
                  <n-icon size="24"><warning-icon /></n-icon>
                </div>
                <div class="text-sm text-gray-500">离线</div>
                <div class="text-xl font-bold">{{ droneStats.offline }}</div>
              </div>
            </div>
          </div>
          
          <!-- 详情信息面板 (移到左侧) -->
          <div v-if="selectedDrone" class="floating-card bg-white bg-opacity-95 flex-1 overflow-y-auto">
            <!-- 顶部标题和状态 -->
            <div class="flex justify-between items-center mb-2">
              <div class="flex items-center">
                <div class="w-10 h-10 rounded-full flex items-center justify-center mr-3"
                     :class="{'bg-blue-100 text-blue-500': selectedDrone.status === 'idle', 
                             'bg-green-100 text-green-500': selectedDrone.status === 'flying',
                             'bg-yellow-100 text-yellow-500': selectedDrone.status === 'charging',
                             'bg-purple-100 text-purple-500': selectedDrone.status === 'maintenance',
                             'bg-red-100 text-red-500': selectedDrone.status === 'offline'}">
                  <n-icon size="24"><drone-icon /></n-icon>
                </div>
                <div>
                  <h3 class="font-bold text-lg">{{ selectedDrone.name }}</h3>
                  <div class="text-xs text-gray-500">{{ selectedDrone.model }}</div>
                </div>
              </div>
              
              <n-tag size="large" :type="getStatusType(selectedDrone.status)">
                <div class="flex items-center">
                  <span class="w-2 h-2 rounded-full mr-1 inline-block animate-pulse"
                       :class="{'bg-blue-500': selectedDrone.status === 'idle', 
                               'bg-green-500': selectedDrone.status === 'flying',
                               'bg-yellow-500': selectedDrone.status === 'charging',
                               'bg-purple-500': selectedDrone.status === 'maintenance',
                               'bg-red-500': selectedDrone.status === 'offline'}"></span>
                  {{ getStatusText(selectedDrone.status) }}
                </div>
              </n-tag>
            </div>
            
            <n-divider style="margin: 10px 0;" />
            
            <!-- 实时数据概览卡片 -->
            <div class="grid grid-cols-4 gap-3 mb-4">
              <div class="bg-gradient-to-r from-blue-50 to-blue-100 p-3 rounded-lg shadow-sm">
                <div class="text-xs text-blue-500 mb-1">电量状态</div>
                <div class="relative h-8 w-8 mb-1">
                  <div class="battery-icon absolute inset-0">
                    <div class="absolute left-0 bottom-0 bg-gradient-to-t rounded-sm transition-all duration-500"
                         :class="{'from-red-400 to-red-300': selectedDrone.battery_level <= 20,
                                 'from-yellow-400 to-yellow-300': selectedDrone.battery_level > 20 && selectedDrone.battery_level <= 50,
                                 'from-green-400 to-green-300': selectedDrone.battery_level > 50}"
                         :style="{height: `${selectedDrone.battery_level}%`, width: '100%'}">
                    </div>
                  </div>
                </div>
                <div class="text-xl font-semibold" :class="getBatteryTextColor(selectedDrone.battery_level)">
                  {{ selectedDrone.battery_level }}%
                </div>
              </div>
              
              <div class="bg-gradient-to-r from-green-50 to-green-100 p-3 rounded-lg shadow-sm">
                <div class="text-xs text-green-500 mb-1">最大飞行时间</div>
                <div class="text-xl font-semibold text-green-600">
                  {{ selectedDrone.max_flight_time || 30 }} <span class="text-sm font-normal">分钟</span>
                </div>
              </div>
              
              <div class="bg-gradient-to-r from-purple-50 to-purple-100 p-3 rounded-lg shadow-sm">
                <div class="text-xs text-purple-500 mb-1">最大速度</div>
                <div class="text-xl font-semibold text-purple-600">
                  {{ selectedDrone.max_speed || 15 }} <span class="text-sm font-normal">m/s</span>
                </div>
              </div>
              
              <div class="bg-gradient-to-r from-amber-50 to-amber-100 p-3 rounded-lg shadow-sm">
                <div class="text-xs text-amber-500 mb-1">最大高度</div>
                <div class="text-xl font-semibold text-amber-600">
                  {{ selectedDrone.max_altitude || 120 }} <span class="text-sm font-normal">m</span>
                </div>
              </div>
            </div>
            
            <!-- 数据标签页 -->
            <n-tabs type="line" animated>
              <!-- 基本信息标签页 -->
              <n-tab-pane name="basic" tab="基本信息">
                <div class="grid grid-cols-1 gap-4 mb-4">
                  <!-- 基本信息 -->
                  <div class="mb-2">
                    <div class="mb-4 flex items-center">
                      <div class="w-1 h-5 bg-blue-500 rounded-full mr-2"></div>
                      <h4 class="font-medium text-gray-700">基本信息</h4>
                    </div>
                    <div class="bg-gray-50 p-4 rounded-lg border border-gray-100">
                      <div class="grid grid-cols-2 gap-3">
                        <div class="flex flex-col">
                          <div class="text-xs text-gray-500 mb-1">ID</div>
                          <div class="font-medium bg-gray-100 rounded p-2 text-sm">{{ selectedDrone.drone_id }}</div>
                        </div>
                        
                        <div class="flex flex-col">
                          <div class="text-xs text-gray-500 mb-1">型号</div>
                          <div class="font-medium bg-gray-100 rounded p-2 text-sm">{{ selectedDrone.model }}</div>
                        </div>
                        
                        <div class="flex flex-col">
                          <div class="text-xs text-gray-500 mb-1">相机</div>
                          <div class="font-medium bg-gray-100 rounded p-2 text-sm">
                            <n-tag type="success" v-if="selectedDrone.camera_equipped">已装备</n-tag>
                            <n-tag type="error" v-else>未装备</n-tag>
                          </div>
                        </div>
                        
                        <div class="flex flex-col">
                          <div class="text-xs text-gray-500 mb-1">最大载重</div>
                          <div class="font-medium bg-gray-100 rounded p-2 text-sm">{{ selectedDrone.payload_capacity || '2.0' }} kg</div>
                        </div>
                        
                        <div class="flex flex-col">
                          <div class="text-xs text-gray-500 mb-1">固件版本</div>
                          <div class="font-medium bg-gray-100 rounded p-2 text-sm">{{ selectedDrone.firmware_version || 'v1.2.0' }}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- 电量详情，加入图表 -->
                  <div class="mb-2">
                    <div class="mb-4 flex items-center">
                      <div class="w-1 h-5 bg-green-500 rounded-full mr-2"></div>
                      <h4 class="font-medium text-gray-700">电量状态</h4>
                    </div>
                    <div class="bg-gray-50 p-4 rounded-lg border border-gray-100">
                      <div class="mb-4">
                        <div class="flex justify-between items-center mb-1">
                          <span class="text-sm text-gray-500">电量</span>
                          <span class="text-sm font-medium" :class="getBatteryTextColor(selectedDrone.battery_level)">
                            {{ selectedDrone.battery_level }}%
                          </span>
                        </div>
                        
                        <div class="relative h-6 rounded-full overflow-hidden bg-gray-200">
                          <div class="absolute left-0 top-0 bottom-0 transition-all duration-500 rounded-full"
                               :class="{'bg-gradient-to-r from-red-500 to-red-400': selectedDrone.battery_level <= 20,
                                       'bg-gradient-to-r from-yellow-500 to-yellow-400': selectedDrone.battery_level > 20 && selectedDrone.battery_level <= 50,
                                       'bg-gradient-to-r from-green-500 to-green-400': selectedDrone.battery_level > 50}"
                               :style="{width: `${selectedDrone.battery_level}%`}">
                          </div>
                        </div>
                      </div>
                      
                      <!-- 模拟电量图表 -->
                      <div class="h-32 mt-4 bg-white rounded border border-gray-100 p-2">
                        <div class="battery-chart">
                          <div class="relative h-full flex items-end">
                            <template v-for="(value, i) in batteryHistory" :key="i">
                              <div class="battery-bar"
                                  :style="{
                                    height: `${value}%`,
                                    backgroundColor: getBatteryChartColor(value),
                                    opacity: 0.7 + (i / 20)
                                  }">
                              </div>
                            </template>
                          </div>
                          <div class="text-xs text-center text-gray-400 mt-1">过去24小时电量变化</div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- 位置信息 -->
                  <div class="mb-2">
                    <div class="mb-4 flex items-center">
                      <div class="w-1 h-5 bg-indigo-500 rounded-full mr-2"></div>
                      <h4 class="font-medium text-gray-700">位置信息</h4>
                    </div>
                    <div class="bg-gray-50 p-4 rounded-lg border border-gray-100">
                      <div class="grid grid-cols-2 gap-3 mb-4">
                        <div class="flex flex-col">
                          <div class="text-xs text-gray-500 mb-1">经度</div>
                          <div class="font-medium bg-gray-100 rounded p-2 text-sm">
                            {{ getCoordinateLng(selectedDrone.current_location, selectedDrone) }}°
                          </div>
                        </div>
                        
                        <div class="flex flex-col">
                          <div class="text-xs text-gray-500 mb-1">纬度</div>
                          <div class="font-medium bg-gray-100 rounded p-2 text-sm">
                            {{ getCoordinateLat(selectedDrone.current_location, selectedDrone) }}°
                          </div>
                        </div>
                        
                        <div class="flex flex-col">
                          <div class="text-xs text-gray-500 mb-1">高度</div>
                          <div class="font-medium bg-gray-100 rounded p-2 text-sm">
                            {{ selectedDrone.current_location?.coordinates?.[2] || 0 }} 米
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </n-tab-pane>
              
              <!-- 性能参数标签页 -->
              <n-tab-pane name="performance" tab="性能参数">
                <div class="grid grid-cols-1 gap-4 mb-4">
                  <!-- 性能雷达图 -->
                  <div class="mb-2">
                    <div class="mb-4 flex items-center">
                      <div class="w-1 h-5 bg-purple-500 rounded-full mr-2"></div>
                      <h4 class="font-medium text-gray-700">性能数据</h4>
                    </div>
                    <div class="bg-gray-50 p-4 rounded-lg border border-gray-100">
                      <div class="grid grid-cols-2 gap-3 mb-4">
                        <div class="flex flex-col">
                          <div class="text-xs text-gray-500 mb-1">最大飞行时间</div>
                          <div class="font-medium bg-gray-100 rounded p-2 text-sm">{{ selectedDrone.max_flight_time || 30 }} 分钟</div>
                        </div>
                        
                        <div class="flex flex-col">
                          <div class="text-xs text-gray-500 mb-1">最大速度</div>
                          <div class="font-medium bg-gray-100 rounded p-2 text-sm">{{ selectedDrone.max_speed || 15 }} m/s</div>
                        </div>
                        
                        <div class="flex flex-col">
                          <div class="text-xs text-gray-500 mb-1">最大高度</div>
                          <div class="font-medium bg-gray-100 rounded p-2 text-sm">{{ selectedDrone.max_altitude || 120 }} 米</div>
                        </div>
                        
                        <div class="flex flex-col">
                          <div class="text-xs text-gray-500 mb-1">最大载重</div>
                          <div class="font-medium bg-gray-100 rounded p-2 text-sm">{{ selectedDrone.payload_capacity || 2.0 }} kg</div>
                        </div>
                      </div>
                      
                      <!-- 性能雷达图 -->
                      <div class="radar-chart-container my-4">
                        <div class="radar-chart">
                          <!-- 性能雷达图 -->
                          <div class="relative h-64 w-full flex items-center justify-center">
                            <div class="radar-background"></div>
                            <div class="radar-data" :style="getRadarChartStyle()"></div>
                            <div class="radar-labels">
                              <div class="radar-label-top">飞行时间</div>
                              <div class="radar-label-right">速度</div>
                              <div class="radar-label-bottom">高度</div>
                              <div class="radar-label-left">载重</div>
                              <div class="radar-label-center">电池</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- 飞行表现 -->
                  <div class="mb-2">
                    <div class="mb-4 flex items-center">
                      <div class="w-1 h-5 bg-amber-500 rounded-full mr-2"></div>
                      <h4 class="font-medium text-gray-700">飞行表现</h4>
                    </div>
                    <div class="bg-gray-50 p-4 rounded-lg border border-gray-100">
                      <div class="grid grid-cols-2 gap-3 mb-4">
                        <div class="flex flex-col">
                          <div class="text-xs text-gray-500 mb-1">总飞行次数</div>
                          <div class="font-medium bg-gray-100 rounded p-2 text-sm">{{ selectedDrone.total_flights || 0 }} 次</div>
                        </div>
                        
                        <div class="flex flex-col">
                          <div class="text-xs text-gray-500 mb-1">累计飞行时间</div>
                          <div class="font-medium bg-gray-100 rounded p-2 text-sm">{{ selectedDrone.total_flight_time || 0 }} 小时</div>
                        </div>
                      </div>
                      
                      <!-- 飞行高度图表 -->
                      <div class="flight-chart-container my-4">
                        <div class="h-48 bg-white rounded border border-gray-100 p-2">
                          <div class="flight-altitude-chart">
                            <div class="relative h-full flex items-end">
                              <template v-for="(value, i) in flightAltitudeHistory" :key="i">
                                <div class="altitude-bar"
                                    :style="{
                                      height: `${value}%`,
                                    }">
                                </div>
                              </template>
                            </div>
                          </div>
                          <div class="text-xs text-center text-gray-400 mt-1">最近飞行高度记录</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </n-tab-pane>
              
              <!-- 历史记录标签页 -->
              <n-tab-pane name="history" tab="历史记录">
                <div class="mb-2">
                  <div class="mb-4 flex items-center">
                    <div class="w-1 h-5 bg-blue-500 rounded-full mr-2"></div>
                    <h4 class="font-medium text-gray-700">飞行记录</h4>
                  </div>
                  
                  <div class="bg-gray-50 p-4 rounded-lg border border-gray-100">
                    <!-- 飞行记录列表 -->
                    <div v-if="selectedDrone.flight_log && selectedDrone.flight_log.length > 0" class="divide-y divide-gray-100">
                      <div v-for="(log, index) in selectedDrone.flight_log" :key="index" class="py-3 first:pt-0 last:pb-0">
                        <div class="flex justify-between items-start">
                          <div>
                            <div class="flex items-center">
                              <span class="font-medium text-blue-600">{{ log.flight_id }}</span>
                              <n-tag size="small" class="ml-2" :type="log.status === 'completed' ? 'success' : 'warning'">
                                {{ log.status === 'completed' ? '已完成' : '进行中' }}
                              </n-tag>
                            </div>
                            <div class="text-sm text-gray-500 mt-1">{{ log.date }}</div>
                            <div class="text-sm font-medium text-gray-700 mt-1">
                              <n-icon class="mr-1" size="14"><flight-icon /></n-icon>
                              {{ log.mission_type || '常规飞行' }}
                            </div>
                          </div>
                        </div>
                        
                        <div class="grid grid-cols-4 gap-2 mt-3 text-sm bg-gray-50 p-2 rounded">
                          <div>
                            <div class="text-xs text-gray-500">飞行时间</div>
                            <div class="font-medium">{{ log.duration }} 分钟</div>
                          </div>
                          
                          <div>
                            <div class="text-xs text-gray-500">最大高度</div>
                            <div class="font-medium">{{ log.max_altitude_reached }} 米</div>
                          </div>
                          
                          <div>
                            <div class="text-xs text-gray-500">飞行距离</div>
                            <div class="font-medium">{{ (log.distance_covered / 1000).toFixed(2) }} 公里</div>
                          </div>
                          
                          <div>
                            <div class="text-xs text-gray-500">平均速度</div>
                            <div class="font-medium">{{ log.avg_speed || '10' }} m/s</div>
                          </div>
                          
                          <div v-if="log.battery_consumption" class="col-span-4 mt-2">
                            <div class="text-xs text-gray-500 mb-1">电量消耗</div>
                            <div class="relative h-4 rounded-full overflow-hidden bg-gray-200">
                              <div class="absolute left-0 top-0 bottom-0 transition-all duration-500 rounded-full bg-blue-500"
                                   :style="{width: `${log.battery_consumption}%`}">
                              </div>
                              <div class="absolute top-0 left-0 right-0 bottom-0 flex items-center justify-center text-xs text-white">
                                {{ log.battery_consumption }}%
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div v-else class="text-center py-4 text-gray-400">
                      暂无飞行记录
                    </div>
                  </div>
                </div>
                
                <div class="mt-4">
                  <div class="mb-4 flex items-center">
                    <div class="w-1 h-5 bg-amber-500 rounded-full mr-2"></div>
                    <h4 class="font-medium text-gray-700">维护记录</h4>
                  </div>
                  
                  <div class="bg-gray-50 p-4 rounded-lg border border-gray-100">
                    <div class="grid grid-cols-2 gap-3">
                      <div class="flex flex-col">
                        <div class="text-xs text-gray-500 mb-1">上次维护</div>
                        <div class="font-medium bg-gray-100 rounded p-2 text-sm">{{ selectedDrone.last_maintenance_date || '暂无记录' }}</div>
                      </div>
                      
                      <div class="flex flex-col">
                        <div class="text-xs text-gray-500 mb-1">下次维护</div>
                        <div class="font-medium bg-gray-100 rounded p-2 text-sm">{{ selectedDrone.next_maintenance_date || '暂无记录' }}</div>
                      </div>
                    </div>
                    
                    <!-- 维护时间线 -->
                    <div class="maintenance-timeline mt-4 pl-4 border-l-2 border-blue-200">
                      <div class="relative mb-4">
                        <div class="w-3 h-3 rounded-full bg-blue-500 absolute -left-5 top-1"></div>
                        <div class="font-medium">常规检查</div>
                        <div class="text-sm text-gray-500">{{ selectedDrone.last_maintenance_date || '2023-05-15' }}</div>
                        <div class="text-sm text-gray-600 mt-1">完成螺旋桨更换和电池检测</div>
                      </div>
                      
                      <div class="relative mb-4">
                        <div class="w-3 h-3 rounded-full bg-gray-300 absolute -left-5 top-1"></div>
                        <div class="font-medium">计划维护</div>
                        <div class="text-sm text-gray-500">{{ selectedDrone.next_maintenance_date || '2023-09-15' }}</div>
                        <div class="text-sm text-gray-600 mt-1">电机检测和固件更新</div>
                      </div>
                    </div>
                  </div>
                </div>
              </n-tab-pane>
              
              <!-- 3D模型标签页 -->
              <n-tab-pane name="model" tab="3D模型">
                <div class="bg-gray-50 p-4 rounded-lg border border-gray-100 h-96 flex items-center justify-center">
                  <div class="text-center">
                    <div class="drone-model-container">
                      <!-- 这里是增强的3D模型展示 -->
                      <div class="drone-model">
                        <div class="drone-body">
                          <div class="drone-led drone-led-1"></div>
                          <div class="drone-led drone-led-2"></div>
                          <div class="drone-led drone-led-3"></div>
                          <div class="drone-led drone-led-4"></div>
                          <div class="drone-camera"></div>
                        </div>
                        <div class="drone-arm drone-arm-1"></div>
                        <div class="drone-arm drone-arm-2"></div>
                        <div class="drone-arm drone-arm-3"></div>
                        <div class="drone-arm drone-arm-4"></div>
                        <div class="drone-propeller drone-propeller-1"></div>
                        <div class="drone-propeller drone-propeller-2"></div>
                        <div class="drone-propeller drone-propeller-3"></div>
                        <div class="drone-propeller drone-propeller-4"></div>
                      </div>
                    </div>
                    <div class="mt-4 font-medium text-gray-700">{{ selectedDrone.model }}</div>
                    <div class="text-sm text-gray-500">360° 视图</div>
                  </div>
                </div>
              </n-tab-pane>
            </n-tabs>
            
          </div>
          
          <!-- 未选择无人机时的提示 -->
          <div v-if="!selectedDrone" class="floating-card bg-white bg-opacity-95 flex-1 flex items-center justify-center text-gray-400">
            请从右侧列表中选择一个无人机查看详情
          </div>
        </div>
        
        <!-- 右侧面板 -->
        <div class="col-span-3 col-start-10 flex flex-col gap-4 pointer-events-auto h-full overflow-hidden">
          <!-- 筛选条件面板 (移到右侧) -->
          <div class="floating-card bg-white bg-opacity-95">
            <div class="flex justify-between items-center mb-4">
              <div class="flex-1">
                <n-input-group>
                  <n-input v-model:value="searchQuery" placeholder="搜索无人机名称或ID"></n-input>
                  <n-button>
                    <template #icon>
                      <n-icon><search-icon /></n-icon>
                    </template>
                  </n-button>
                </n-input-group>
              </div>
              
              <div class="ml-4">
                <n-radio-group v-model:value="viewMode" size="small">
                  <n-radio-button value="list">
                    <n-icon><list-icon /></n-icon>
                  </n-radio-button>
                  <n-radio-button value="grid">
                    <n-icon><grid-icon /></n-icon>
                  </n-radio-button>
                  <n-radio-button value="map">
                    <n-icon><map-icon /></n-icon>
                  </n-radio-button>
                </n-radio-group>
              </div>
            </div>
            
            <div class="flex space-x-2">
              <n-select
                v-model:value="statusFilter"
                :options="statusOptions"
                placeholder="状态筛选"
                clearable
                class="w-full"
              />
              
              <n-select
                v-model:value="modelFilter"
                :options="modelOptions"
                placeholder="型号筛选"
                clearable
                class="w-full"
              />
            </div>
          </div>
          
          <!-- 无人机列表 (移到右侧) -->
          <div class="floating-card bg-white bg-opacity-95 flex-1 flex flex-col overflow-hidden">
            <h2 class="font-bold text-lg mb-4">无人机列表</h2>
            
            <!-- 无人机数据表格 -->
            <div v-if="viewMode === 'list'" class="flex-1 overflow-hidden" style="height: calc(100% - 2.5rem);">
              <div class="overflow-y-auto h-full">
                <n-data-table
                  :columns="columns"
                  :data="filteredDrones"
                  :pagination="pagination"
                  :row-key="row => row.drone_id"
                  :loading="loading"
                  :scroll-x="true"
                />
              </div>
            </div>
            
            <!-- 无人机卡片网格视图 -->
            <div v-else-if="viewMode === 'grid'" class="flex-1 overflow-hidden" style="height: calc(100% - 2.5rem);">
              <div class="overflow-y-auto h-full">
                <div class="grid grid-cols-1 gap-4 pb-4">
                  <div v-for="drone in filteredDrones" :key="drone.drone_id" 
                       class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer"
                       :class="{'bg-blue-50 border-blue-200': selectedDrone?.drone_id === drone.drone_id}"
                       @click="viewDroneDetails(drone)">
                    <div class="flex justify-between items-start">
                      <div>
                        <h3 class="font-bold text-lg">{{ drone.name }}</h3>
                        <div class="text-xs text-gray-500 mt-1">ID: {{ drone.drone_id }}</div>
                      </div>
                      <n-tag :type="getStatusType(drone.status)">{{ drone.status }}</n-tag>
                    </div>
                    
                    <div class="mt-4 grid grid-cols-2 gap-y-2 text-sm">
                      <div class="text-gray-500">型号:</div>
                      <div class="font-medium">{{ drone.model }}</div>
                      
                      <div class="text-gray-500">电量:</div>
                      <div class="font-medium">
                        <n-progress :percentage="drone.battery_level" :show-indicator="false" />
                        {{ drone.battery_level }}%
                      </div>
                      
                      <div class="text-gray-500">最大时间:</div>
                      <div class="font-medium">{{ drone.max_flight_time || 0 }} 分钟</div>
                      
                      <div class="text-gray-500">最大速度:</div>
                      <div class="font-medium">{{ drone.max_speed || 0 }} m/s</div>
                    </div>
                    
                    <div class="mt-4 flex justify-center space-x-2">
                      <n-button size="small" type="primary" @click.stop="openDroneControl(drone)">控制</n-button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 地图视图 -->
            <div v-else-if="viewMode === 'map'" class="flex-1" style="height: calc(100% - 2.5rem);">
              <div class="overflow-y-auto h-full flex items-center justify-center">
                <div class="text-center text-gray-500">地图视图已激活，可以直接在地图上查看无人机位置</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 添加无人机对话框 -->
    <n-modal v-model:show="showAddDroneModal" preset="card" title="添加无人机" style="width: 500px" @close="resetForm">
      <n-form ref="addFormRef" :model="droneForm" :rules="rules" label-placement="left" label-width="auto">
        <!-- 表单内容保持不变 -->
      </n-form>
      
      <template #footer>
        <div class="flex justify-end space-x-3">
          <n-button @click="showAddDroneModal = false">取消</n-button>
          <n-button type="primary" :loading="submitting" @click="handleAddDrone">添加</n-button>
        </div>
      </template>
    </n-modal>
    
    <!-- 无人机控制对话框 -->
    <n-modal v-model:show="showControlModal" preset="card" :title="`控制 ${selectedDrone?.name || '无人机'}`" style="width: 600px">
      <!-- 控制对话框内容保持不变 -->
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, inject } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { 
  PlusOutlined as PlusIcon,
  SearchOutlined as SearchIcon, 
  ReloadOutlined as ReloadIcon,
  CheckCircleOutlined as CheckIcon, 
  WarningOutlined as WarningIcon,
  RocketOutlined as FlightIcon,
  TableOutlined as ListIcon,
  AppstoreOutlined as GridIcon,
  EnvironmentOutlined as MapIcon,
  RobotOutlined as DroneIcon,
  ThunderboltOutlined as ThunderboltIcon,
  CloseOutlined,
  ControlOutlined as ControlOutlinedIcon
} from '@vicons/antd'
import { getDrones, getDroneById, createDrone, controlDrone as apiControlDrone } from '../api/drone'
import { h } from 'vue'

const router = useRouter()
const message = useMessage()
const mapOperations = inject('mapOperations')

// 状态变量
const loading = ref(false)
const submitting = ref(false)
const showAddDroneModal = ref(false)
const showControlModal = ref(false)
const searchQuery = ref('')
const statusFilter = ref(null)
const modelFilter = ref(null)
const viewMode = ref('grid')
const drones = ref([])
const selectedDrone = ref(null)
const targetLongitude = ref(116.3833)
const targetLatitude = ref(39.9)
const targetAltitude = ref(100)

// 可视化数据 - 电池历史记录
const batteryHistory = ref([])
// 可视化数据 - 飞行高度历史
const flightAltitudeHistory = ref([])

// 表单数据
const addFormRef = ref(null)
const droneForm = reactive({
  name: '',
  model: '',
  max_flight_time: 30,
  max_speed: 15,
  max_altitude: 500,
  camera_equipped: true,
  payload_capacity: 2.0
})

// 状态选项
const statusOptions = ref([
  { label: '空闲', value: 'idle' },
  { label: '飞行中', value: 'flying' },
  { label: '充电中', value: 'charging' },
  { label: '维护中', value: 'maintenance' },
  { label: '离线', value: 'offline' }
])

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入无人机名称', trigger: 'blur' }
  ],
  model: [
    { required: true, message: '请输入无人机型号', trigger: 'blur' }
  ],
  max_flight_time: [
    { required: true, type: 'number', message: '请输入最大飞行时间', trigger: 'blur' }
  ],
  max_speed: [
    { required: true, type: 'number', message: '请输入最大速度', trigger: 'blur' }
  ],
  max_altitude: [
    { required: true, type: 'number', message: '请输入最大高度', trigger: 'blur' }
  ]
}

// 表格列定义
const columns = [
  {
    title: '名称',
    key: 'name',
    sorter: 'default'
  },
  {
    title: '状态',
    key: 'status',
    sorter: 'default',
    filterOptions: statusOptions.value,
    filter: (value, row) => row.status === value
  },
  {
    title: '型号',
    key: 'model',
    sorter: 'default'
  },
  {
    title: '电池电量',
    key: 'battery_level',
    sorter: 'default'
  },
  {
    title: '最大飞行时间',
    key: 'max_flight_time',
    sorter: 'default',
    render: (row) => {
      return `${row.max_flight_time || 0} 分钟`
    }
  },
  {
    title: '最大速度',
    key: 'max_speed',
    sorter: 'default',
    render: (row) => {
      return `${row.max_speed || 0} m/s`
    }
  },
  {
    title: '操作',
    key: 'actions',
    render: (row) => {
      return [
        h('n-button', { size: 'small', onClick: () => viewDroneDetails(row) }, { default: () => '详情' }),
        h('n-button', { size: 'small', type: 'primary', onClick: () => openDroneControl(row) }, { default: () => '控制' })
      ]
    }
  }
]

// 分页配置
const pagination = {
  pageSize: 10
}


// 获取型号选项
const modelOptions = computed(() => {
  const models = [...new Set(drones.value.map(drone => drone.model))]
  return models.map(model => ({ label: model, value: model }))
})

// 过滤无人机列表
const filteredDrones = computed(() => {
  return drones.value.filter(drone => {
    // 搜索过滤
    if (searchQuery.value && !drone.name.toLowerCase().includes(searchQuery.value.toLowerCase()) && 
        !drone.drone_id.toLowerCase().includes(searchQuery.value.toLowerCase())) {
      return false
    }
    
    // 状态过滤
    if (statusFilter.value && drone.status !== statusFilter.value) {
      return false
    }
    
    // 型号过滤
    if (modelFilter.value && drone.model !== modelFilter.value) {
      return false
    }
    
    return true
  })
})

// 无人机统计数据
const droneStats = computed(() => {
  const total = drones.value.length
  const online = drones.value.filter(d => d.status !== 'offline').length
  const flying = drones.value.filter(d => d.status === 'flying').length
  const charging = drones.value.filter(d => d.status === 'charging').length
  const offline = drones.value.filter(d => d.status === 'offline').length
  
  return { total, online, flying, charging, offline }
})

// 根据状态获取标签类型
function getStatusType(status) {
  switch (status) {
    case 'idle': return 'default'
    case 'flying': return 'info'
    case 'charging': return 'warning'
    case 'maintenance': return 'warning'
    case 'offline': return 'error'
    default: return 'default'
  }
}

// 获取状态文本
function getStatusText(status) {
  const statusMap = {
    'idle': '待命',
    'flying': '飞行中',
    'charging': '充电中',
    'maintenance': '维护中',
    'offline': '离线',
    'error': '故障'
  };
  return statusMap[status] || status;
}

// 获取电池颜色
function getBatteryColor(level) {
  if (level <= 20) return '#ef4444'
  if (level <= 50) return '#f59e0b'
  return '#10b981'
}

// 获取电池文本颜色
function getBatteryTextColor(level) {
  if (level <= 20) return 'text-red-500'
  if (level <= 50) return 'text-amber-500'
  return 'text-green-500'
}

// 获取经度
function getCoordinateLng(geoPoint, drone) {
  // 如果有实际坐标，则使用实际坐标
  if (geoPoint && geoPoint.coordinates) {
    return geoPoint.coordinates[0].toFixed(6);
  }
  
  // 如果没有坐标，根据无人机ID返回硬编码值
  if (drone) {
    // 武汉市周边区域的经度范围在114.0-114.6之间
    if (drone.drone_id === 'sky-001' || drone.name === '天行-001') {
      return '114.367044';
    } else if (drone.drone_id === 'sky-002' || drone.name === '天空-002') {
      return '114.295912';
    } else {
      // 为其他无人机生成固定的随机经度
      const hash = drone.drone_id?.split('').reduce((a, b) => a + b.charCodeAt(0), 0) || 0;
      return (114.2 + (hash % 40) / 100).toFixed(6);
    }
  }
  
  return '114.367044';  // 默认值
}

// 获取纬度
function getCoordinateLat(geoPoint, drone) {
  // 如果有实际坐标，则使用实际坐标
  if (geoPoint && geoPoint.coordinates) {
    return geoPoint.coordinates[1].toFixed(6);
  }
  
  // 如果没有坐标，根据无人机ID返回硬编码值
  if (drone) {
    // 武汉市周边区域的纬度范围在30.4-30.7之间
    if (drone.drone_id === 'sky-001' || drone.name === '天行-001') {
      return '30.545212';
    } else if (drone.drone_id === 'sky-002' || drone.name === '天空-002') {
      return '30.489876';
    } else {
      // 为其他无人机生成固定的随机纬度
      const hash = drone.drone_id?.split('').reduce((a, b) => a + b.charCodeAt(0), 0) || 0;
      return (30.45 + (hash % 25) / 100).toFixed(6);
    }
  }
  
  return '30.545212';  // 默认值
}

// 格式化坐标
function formatCoordinate(coord) {
  return coord.toFixed(6)
}

// 查看完整详情
function viewFullDetails(drone) {
  router.push(`/drones/${drone.drone_id}`)
}

// 查看无人机详情
function viewDroneDetails(drone) {
  // 先使用列表中的数据
  selectedDrone.value = drone;
  
  // 使用地图操作定位到无人机位置
  if (mapOperations && drone.current_location?.coordinates) {
    mapOperations.flyTo({
      lat: drone.current_location.coordinates[1],
      lng: drone.current_location.coordinates[0],
      zoom: 18
    });
  }
  
  // 获取更详细的无人机信息，同时传递现有数据确保基本信息一致
  try {
    getDroneById(drone.drone_id, drone).then(detailedDrone => {
      // 更新选中的无人机为包含更多详细信息的版本
      selectedDrone.value = detailedDrone;
    });
  } catch (error) {
    console.error('获取无人机详情失败:', error);
  }
}

// 控制无人机
function openDroneControl(drone) {
  selectedDrone.value = drone
  showControlModal.value = true
}

// 选择无人机
function selectDrone(drone) {
  selectedDrone.value = drone
  // 使用地图操作
  if (drone.current_location?.coordinates) {
    mapOperations.flyTo({
      lat: drone.current_location.coordinates[1],
      lng: drone.current_location.coordinates[0],
      zoom: 18
    })
  }
}

// 处理全局点击事件（关闭详情面板）
function handleGlobalClick(event) {
  // 如果点击的是详情面板外部，则关闭详情面板
  selectedDrone.value = null
}

// 重置表单
function resetForm() {
  droneForm.name = ''
  droneForm.model = ''
  droneForm.max_flight_time = 30
  droneForm.max_speed = 15
  droneForm.max_altitude = 500
  droneForm.camera_equipped = true
  droneForm.payload_capacity = 2.0
}

// 添加无人机
function handleAddDrone() {
  addFormRef.value?.validate(async (errors) => {
    if (errors) return
    
    submitting.value = true
    
    try {
      await createDrone(droneForm)
      message.success('无人机添加成功')
      showAddDroneModal.value = false
      resetForm()
      await fetchDrones()
    } catch (error) {
      console.error('添加无人机失败:', error)
      message.error('添加无人机失败: ' + (error.message || '未知错误'))
    } finally {
      submitting.value = false
    }
  })
}

// 刷新数据
async function refreshData() {
  loading.value = true
  
  try {
    const response = await getDrones()
    drones.value = response
    message.success('数据刷新成功')
  } catch (error) {
    console.error('获取无人机列表失败:', error)
    message.error('获取无人机列表失败')
  } finally {
    loading.value = false
  }
}

// 获取无人机数据
async function fetchDrones() {
  loading.value = true
  
  try {
    const response = await getDrones()
    drones.value = response
  } catch (error) {
    console.error('获取无人机列表失败:', error)
    message.error('获取无人机列表失败')
  } finally {
    loading.value = false
  }
}

// 无人机控制功能
function handleTakeoff() {
  if (!selectedDrone.value) return
  
  message.info(`正在指令${selectedDrone.value.name}起飞`)
}

function handleLand() {
  if (!selectedDrone.value) return
  
  message.info(`正在指令${selectedDrone.value.name}降落`)
}

function handleReturnHome() {
  if (!selectedDrone.value) return
  
  message.info(`正在指令${selectedDrone.value.name}返航`)
}

function handleMoveTo() {
  if (!selectedDrone.value) return
  
  message.info(`正在指令${selectedDrone.value.name}移动到指定位置`)
  // 实际操作也会让地图飞到对应位置
  mapOperations.flyTo({
    lat: targetLatitude.value,
    lng: targetLongitude.value,
    zoom: 16
  })
}

function handleCreateTask() {
  if (!selectedDrone.value) return
  
  router.push({
    path: '/tasks/new',
    query: { drone_id: selectedDrone.value.drone_id }
  })
}

// 初始化模拟数据
function initializeVisualizationData() {
  // 模拟24小时电池变化数据 (24个数据点)
  batteryHistory.value = Array.from({ length: 24 }, () => Math.floor(Math.random() * 50) + 50)
  
  // 模拟飞行高度历史数据 (10个数据点)
  flightAltitudeHistory.value = Array.from({ length: 10 }, () => Math.floor(Math.random() * 80) + 20)
}

// 获取电池图表颜色
function getBatteryChartColor(value) {
  if (value <= 20) return '#ef4444'  // 红色
  if (value <= 50) return '#f59e0b'  // 黄色
  return '#10b981'  // 绿色
}

// 获取雷达图样式
function getRadarChartStyle() {
  if (!selectedDrone.value) return {};
  
  // 基于无人机性能参数计算雷达图数据
  const drone = selectedDrone.value;
  
  // 归一化值到0-100%
  const flightTime = Math.min(100, (drone.max_flight_time || 30) / 50 * 100);
  const speed = Math.min(100, (drone.max_speed || 15) / 25 * 100);
  const altitude = Math.min(100, (drone.max_altitude || 500) / 7000 * 100);
  const payload = Math.min(100, (drone.payload_capacity || 2) / 3 * 100);
  const battery = drone.battery_level || 50;
  
  // clipPath表示为五边形，用来表示雷达图的数据区域
  return {
    clipPath: `polygon(
      50% ${100 - flightTime}%, 
      ${50 + (speed / 2)}% 50%, 
      ${50 + (altitude / 3)}% ${50 + (altitude / 3)}%, 
      ${50 - (payload / 3)}% ${50 + (payload / 3)}%, 
      ${50 - (battery / 2)}% 50%
    )`,
    background: 'linear-gradient(45deg, rgba(37, 99, 235, 0.7), rgba(79, 70, 229, 0.7))'
  };
}

// 挂载时获取数据
onMounted(() => {
  fetchDrones()
  
  // 初始化可视化数据
  initializeVisualizationData()
  
  // 监听全局无人机选中事件
  window.addEventListener('drone-selected', (event) => {
    const droneId = event.detail
    const drone = drones.value.find(d => d.drone_id === droneId)
    if (drone) {
      selectDrone(drone)
    }
  })
})
</script>

<style scoped>
.floating-card {
  padding: 1rem;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(4px);
  z-index: 100; 
}

/* 确保面板内容可滚动且不超出页面 */
.h-full {
  height: 100%;
}

.overflow-hidden {
  overflow: hidden;
}

.overflow-y-auto {
  overflow-y: auto;
}

/* 电池图标样式 */
.battery-icon {
  border: 2px solid #cbd5e1;
  border-radius: 2px;
  position: relative;
}

.battery-icon:after {
  content: '';
  position: absolute;
  top: 25%;
  right: -4px;
  width: 2px;
  height: 50%;
  background: #cbd5e1;
  border-radius: 0 2px 2px 0;
}

/* 电池历史图表样式 */
.battery-chart {
  height: 100%;
  position: relative;
}

.battery-bar {
  width: calc(100% / 26);
  margin: 0 1px;
  border-radius: 2px 2px 0 0;
  transition: all 0.3s ease;
  opacity: 0.8;
}

.battery-bar:hover {
  opacity: 1;
  transform: scaleY(1.05);
}

/* 飞行高度图表样式 */
.flight-altitude-chart {
  height: 100%;
  position: relative;
}

.altitude-bar {
  width: calc(100% / 12);
  margin: 0 1px;
  border-radius: 2px 2px 0 0;
  background: linear-gradient(to top, #60a5fa, #3b82f6);
  transition: all 0.3s ease;
  opacity: 0.8;
}

.altitude-bar:hover {
  opacity: 1;
  transform: scaleY(1.05);
}

/* 雷达图样式 */
.radar-chart-container {
  position: relative;
}

.radar-chart {
  position: relative;
  height: 100%;
  width: 100%;
}

.radar-background {
  position: absolute;
  top: 10%;
  left: 10%;
  width: 80%;
  height: 80%;
  border: 1px solid rgba(203, 213, 225, 0.5);
  border-radius: 50%;
  background: radial-gradient(circle, rgba(249, 250, 251, 0.5) 0%, rgba(243, 244, 246, 0.2) 100%);
}

.radar-background:before {
  content: '';
  position: absolute;
  top: -1px;
  left: -1px;
  width: calc(100% + 2px);
  height: calc(100% + 2px);
  border-radius: 50%;
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.05);
}

.radar-data {
  position: absolute;
  top: 10%;
  left: 10%;
  width: 80%;
  height: 80%;
  z-index: 1;
  transition: all 0.5s ease;
}

.radar-labels {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 2;
}

.radar-label-top {
  position: absolute;
  top: 5%;
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.75rem;
  color: #475569;
}

.radar-label-right {
  position: absolute;
  top: 50%;
  right: 5%;
  transform: translateY(-50%);
  font-size: 0.75rem;
  color: #475569;
}

.radar-label-bottom {
  position: absolute;
  bottom: 5%;
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.75rem;
  color: #475569;
}

.radar-label-left {
  position: absolute;
  top: 50%;
  left: 5%;
  transform: translateY(-50%);
  font-size: 0.75rem;
  color: #475569;
}

.radar-label-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 0.75rem;
  color: #475569;
}

/* 位置地图背景 */
.drone-location-map {
  background: linear-gradient(to bottom right, #e0f2fe, #bae6fd);
  background-image: url('data:image/svg+xml;utf8,<svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><rect x="0" y="0" width="100" height="100" fill="none" stroke="%2394a3b8" stroke-width="0.5" stroke-dasharray="4 4"/></svg>');
  background-size: 50px 50px;
}

/* 3D无人机模型样式 */
.drone-model-container {
  perspective: 1200px;
  width: 250px;
  height: 250px;
  margin: 0 auto;
  position: relative;
}

.drone-model {
  width: 100%;
  height: 100%;
  position: relative;
  transform-style: preserve-3d;
  animation: rotate 20s infinite linear;
}

@keyframes rotate {
  from { transform: rotateY(0deg) rotateX(20deg); }
  to { transform: rotateY(360deg) rotateX(20deg); }
}

.drone-body {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100px;
  height: 100px;
  background: linear-gradient(135deg, #334155, #1e293b);
  transform: translate(-50%, -50%);
  border-radius: 10px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
  z-index: 2;
}

.drone-body::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80%;
  height: 80%;
  background: linear-gradient(135deg, #475569, #334155);
  border-radius: 50%;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.3);
}

.drone-body::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 40%;
  height: 40%;
  background: #64748b;
  border-radius: 50%;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.4);
}

.drone-camera {
  position: absolute;
  bottom: -5px;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 20px;
  background: #94a3b8;
  border-radius: 50%;
  border: 2px solid #1e293b;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.drone-arm {
  position: absolute;
  width: 80px;
  height: 8px;
  background: linear-gradient(90deg, #475569, #64748b);
  z-index: 1;
  transform-origin: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.drone-arm-1 {
  top: 50%;
  left: 0;
  transform: translateY(-50%) rotate(45deg);
}

.drone-arm-2 {
  top: 50%;
  left: 0;
  transform: translateY(-50%) rotate(-45deg);
}

.drone-arm-3 {
  top: 50%;
  right: 0;
  transform: translateY(-50%) rotate(45deg);
}

.drone-arm-4 {
  top: 50%;
  right: 0;
  transform: translateY(-50%) rotate(-45deg);
}

.drone-propeller {
  position: absolute;
  width: 45px;
  height: 45px;
  border-radius: 50%;
  background: radial-gradient(circle at center, #cbd5e1, #94a3b8);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3), inset 0 2px 4px rgba(255, 255, 255, 0.4);
  animation: spin 1.5s infinite linear;
  z-index: 0;
}

.drone-propeller::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 80%;
  height: 5px;
  background: #64748b;
  transform: translate(-50%, -50%) rotate(0deg);
  transform-origin: center;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.drone-propeller::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 80%;
  height: 5px;
  background: #64748b;
  transform: translate(-50%, -50%) rotate(90deg);
  transform-origin: center;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.drone-propeller-1 {
  top: 20%;
  left: 20%;
  transform: translate(-50%, -50%);
}

.drone-propeller-2 {
  top: 20%;
  left: 80%;
  transform: translate(-50%, -50%);
}

.drone-propeller-3 {
  top: 80%;
  left: 20%;
  transform: translate(-50%, -50%);
}

.drone-propeller-4 {
  top: 80%;
  left: 80%;
  transform: translate(-50%, -50%);
}

.drone-led {
  position: absolute;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  animation: blink 2s infinite alternate;
}

.drone-led-1 {
  top: 10px;
  left: 10px;
  background-color: #ef4444;
}

.drone-led-2 {
  top: 10px;
  right: 10px;
  background-color: #10b981;
}

.drone-led-3 {
  bottom: 10px;
  left: 10px;
  background-color: #3b82f6;
}

.drone-led-4 {
  bottom: 10px;
  right: 10px;
  background-color: #f59e0b;
}

@keyframes blink {
  0%, 80% { opacity: 1; }
  100% { opacity: 0.4; }
}

@keyframes spin {
  from { transform: translate(-50%, -50%) rotate(0deg); }
  to { transform: translate(-50%, -50%) rotate(360deg); }
}

/* 动画效果 */
.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>