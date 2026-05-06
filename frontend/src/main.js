import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import ECharts from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, PieChart, ScatterChart, LineChart, TreemapChart, CandlestickChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
  DataZoomComponent,
  VisualMapComponent
} from 'echarts/components'

use([
  CanvasRenderer,
  BarChart, PieChart, ScatterChart, LineChart, TreemapChart, CandlestickChart,
  TitleComponent, TooltipComponent, LegendComponent, GridComponent, DatasetComponent, DataZoomComponent, VisualMapComponent
])

const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus)
app.component('v-chart', ECharts)

app.mount('#app')
