/**
 * Deck.gl图层管理模块
 */
import { Deck } from '@deck.gl/core'

/**
 * 初始化Deck.gl实例
 * @param {Object} options 初始化选项
 * @returns {Object} Deck.gl实例
 */
export const initializeDeck = (options = {}) => {
  const {
    map,
    container,
    initialViewState,
    onHover,
    onClick
  } = options

  if (!map) {
    throw new Error('缺少地图实例')
  }

  const deck = new Deck({
    canvas: container || 'deck-canvas',
    width: '100%',
    height: '100%',
    initialViewState: initialViewState || {
      longitude: map.getCenter().lng,
      latitude: map.getCenter().lat,
      zoom: map.getZoom(),
      pitch: map.getPitch(),
      bearing: map.getBearing()
    },
    controller: false,
    onViewStateChange: ({ viewState }) => {
      // 同步视图状态
      map.jumpTo({
        center: [viewState.longitude, viewState.latitude],
        zoom: viewState.zoom,
        bearing: viewState.bearing,
        pitch: viewState.pitch
      })
      return viewState
    },
    layers: [],
    getTooltip: onHover,
    onClick: onClick
  })

  // 确保deckgl可视区域与地图同步
  map.on('render', () => {
    deck.setProps({
      viewState: {
        longitude: map.getCenter().lng,
        latitude: map.getCenter().lat,
        zoom: map.getZoom(),
        pitch: map.getPitch(),
        bearing: map.getBearing()
      }
    })
  })

  return deck
}

/**
 * 创建deck.gl画布并添加到地图容器
 * @param {HTMLElement} mapContainer 地图容器
 * @returns {HTMLElement} 创建的canvas元素
 */
export const createDeckCanvas = (mapContainer) => {
  if (!mapContainer) return null

  // 检查是否已存在
  let deckCanvas = document.getElementById('deck-canvas')
  if (deckCanvas) return deckCanvas

  // 创建canvas
  deckCanvas = document.createElement('canvas')
  deckCanvas.id = 'deck-canvas'
  deckCanvas.style.position = 'absolute'
  deckCanvas.style.top = '0'
  deckCanvas.style.left = '0'
  deckCanvas.style.width = '100%'
  deckCanvas.style.height = '100%'
  deckCanvas.style.pointerEvents = 'none'
  mapContainer.appendChild(deckCanvas)

  return deckCanvas
}

/**
 * 更新deck.gl图层
 * @param {Object} deck deck.gl实例
 * @param {Array} layers 图层数组
 */
export const updateDeckLayers = (deck, layers = []) => {
  if (!deck) return
  deck.setProps({ layers })
} 