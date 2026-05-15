// 匯入 Vue 的 createApp 函式，這是 Vue 3 建立應用程式實體的進入點
import { createApp } from 'vue'

// 匯入全域的 CSS 樣式檔案，定義了基礎的版面配置、字型與深色/淺色主題變數
import './style.css'

// 匯入應用程式的根組件 (Root Component)
import App from './App.vue'

// 匯入 Element Plus UI 元件庫，提供豐富且美觀的基礎元件 (如按鈕、表格、選單等)
import ElementPlus from 'element-plus'
// 匯入 Element Plus 的預設 CSS 樣式
import 'element-plus/dist/index.css'
// 將 Element Plus 提供的所有圖示元件一次性匯入，方便後續在整個專案中使用
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// 匯入 vue-echarts，它是 ECharts 的 Vue 封裝套件，能以組件形式 <v-chart> 輕鬆使用
import ECharts from 'vue-echarts'
// 匯入 ECharts 的核心 use 函式，用於按需引入需要的模組，減小打包體積
import { use } from 'echarts/core'
// 匯入 Canvas 渲染器，ECharts 預設使用 Canvas 繪圖
import { CanvasRenderer } from 'echarts/renderers'
// 按需匯入各種類型的圖表，包含長條圖、圓餅圖、散佈圖、折線圖、樹狀圖、K線圖、儀表與雷達圖
import { BarChart, PieChart, ScatterChart, LineChart, TreemapChart, CandlestickChart, GaugeChart, RadarChart } from 'echarts/charts'
// 按需匯入 ECharts 的各式輔助元件，如標題、提示框、圖例、網格、資料集、縮放軸及視覺映射元件
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
  DataZoomComponent,
  VisualMapComponent
} from 'echarts/components'

// 使用 ECharts 的 use 函式註冊剛剛匯入的所有圖表與元件，讓它們生效
use([
  CanvasRenderer,
  BarChart, PieChart, ScatterChart, LineChart, TreemapChart, CandlestickChart, GaugeChart, RadarChart,
  TitleComponent, TooltipComponent, LegendComponent, GridComponent, DatasetComponent, DataZoomComponent, VisualMapComponent
])

// 建立 Vue 應用程式實體，並掛載 App 根組件
const app = createApp(App)

// 透過 Object.entries 走訪 ElementPlusIconsVue 內所有的圖示，並將它們全域註冊到 Vue 應用中
// 這樣就可以在任何 Vue 檔案內直接使用 <el-icon><圖示名稱 /></el-icon>
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 註冊 Element Plus 套件，使其成為全域可用
app.use(ElementPlus)

// 註冊 ECharts 的 Vue 組件，命名為 'v-chart'，如此一來就能在範本中使用 <v-chart> 標籤
app.component('v-chart', ECharts)

// 將準備好的 Vue 應用程式掛載到 index.html 裡 id 為 'app' 的 DOM 元素上
app.mount('#app')
