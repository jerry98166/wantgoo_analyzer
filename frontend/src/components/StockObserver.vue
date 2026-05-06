<template>
  <div>
    <h2>個股籌碼指標 (全方位技術面+籌碼面)</h2>
    <p>結合最完整的 K 線圖與技術指標，並將法人買賣超拆解為「外資、投信、自營商」，更獨家計算了「法人波段預估成本線」，一眼看穿主力底牌。</p>
    
    <el-card shadow="never" style="margin-bottom: 20px; background-color: #fbfbfc;">
      <el-input 
        v-model="stockId" 
        placeholder="請輸入股票代號 (例如: 2330)" 
        style="width: 300px; margin-right: 15px;"
        @keyup.enter="fetchData"
        size="large"
      >
        <template #prepend>代號</template>
      </el-input>
      <el-button type="primary" @click="fetchData" :loading="loading" size="large">開始深度分析</el-button>
    </el-card>

    <div v-if="stockData">
      <el-row :gutter="20" style="margin-bottom: 20px;">
        <el-col :span="24">
          <el-alert
            :title="`AI 階段判定：${stockData.phase}`"
            :type="getPhaseType(stockData.phase)"
            show-icon
            :closable="false"
            style="border-radius: 8px;"
          />
        </el-col>
      </el-row>
      
      <el-row :gutter="20" style="margin-bottom: 20px;">
        <el-col :span="6">
          <el-card shadow="hover" class="data-card">
            <div class="data-title">波段法人預估成本</div>
            <div class="data-value" style="color: #E6A23C">
              {{ stockData.inst_cost > 0 ? stockData.inst_cost : '無明顯買盤' }}
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="data-card">
            <div class="data-title">波段籌碼集中度</div>
            <div class="data-value" style="color: #409EFF">
              {{ stockData.period_participation }}%
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="data-card">
            <div class="data-title">近五日累計買賣超</div>
            <div :class="['data-value', stockData.recent_buys > 0 ? 'text-up' : 'text-down']">
              {{ stockData.recent_buys > 0 ? '+' : '' }}{{ stockData.recent_buys }} 張
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="data-card">
            <div class="data-title">近五日股價變化</div>
            <div :class="['data-value', stockData.recent_price_change_pct > 0 ? 'text-up' : 'text-down']">
              {{ stockData.recent_price_change_pct > 0 ? '+' : '' }}{{ stockData.recent_price_change_pct }}%
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="hover">
        <div class="chart-container">
          <v-chart class="chart" :option="chartOption" autoresize />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'

const stockId = ref('2330')
const loading = ref(false)
const stockData = ref(null)

const getPhaseType = (phase) => {
  if (phase.includes('建倉')) return 'success'
  if (phase.includes('加碼')) return 'info'
  if (phase.includes('獲利了結')) return 'warning'
  if (phase.includes('撤出')) return 'error'
  return 'info'
}

const chartOption = computed(() => {
  if (!stockData.value) return {}
  
  return {
    tooltip: { 
      trigger: 'axis', 
      axisPointer: { type: 'cross' } 
    },
    legend: { 
      data: ['日K線', 'MA5', 'MA20', 'MA60', '外資', '投信', '自營商', 'RSI', 'MACD', 'Signal', 'MACD柱'],
      top: 0
    },
    axisPointer: {
      link: {xAxisIndex: 'all'}
    },
    grid: [
      { left: '8%', right: '5%', top: '8%', height: '35%' },     // K線/均線
      { left: '8%', right: '5%', top: '48%', height: '12%' },    // 法人買賣超拆解
      { left: '8%', right: '5%', top: '65%', height: '12%' },    // RSI
      { left: '8%', right: '5%', top: '82%', height: '12%' }     // MACD
    ],
    xAxis: [
      { type: 'category', data: stockData.value.dates, boundaryGap: false, gridIndex: 0 },
      { type: 'category', data: stockData.value.dates, gridIndex: 1, show: false },
      { type: 'category', data: stockData.value.dates, gridIndex: 2, show: false },
      { type: 'category', data: stockData.value.dates, gridIndex: 3, show: false }
    ],
    yAxis: [
      { type: 'value', name: '價格', gridIndex: 0, scale: true, splitLine: { show: true, lineStyle: { type: 'dashed' } } },
      { type: 'value', name: '籌碼(張)', gridIndex: 1, splitLine: { show: false } },
      { type: 'value', name: 'RSI', gridIndex: 2, splitLine: { show: false }, min: 0, max: 100 },
      { type: 'value', name: 'MACD', gridIndex: 3, splitLine: { show: false } }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1, 2, 3], start: 0, end: 100 },
      { show: true, xAxisIndex: [0, 1, 2, 3], type: 'slider', bottom: '0%' }
    ],
    series: [
      // Grid 0: Price & MA
      {
        name: '日K線',
        type: 'candlestick',
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: {
          color: '#f56c6c',    // TW format: Red for UP
          color0: '#67c23a',   // TW format: Green for DOWN
          borderColor: '#f56c6c',
          borderColor0: '#67c23a'
        },
        markLine: {
          data: stockData.value.inst_cost > 0 ? [
            { 
              yAxis: stockData.value.inst_cost, 
              name: '法人預估成本', 
              lineStyle: { color: '#E6A23C', type: 'solid', width: 2 },
              label: { formatter: '成本: {c}', position: 'end' }
            }
          ] : []
        },
        data: stockData.value.kline_data
      },
      {
        name: 'MA5',
        type: 'line',
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: { color: '#ff9800' },
        lineStyle: { width: 1.5, type: 'solid' },
        showSymbol: false,
        data: stockData.value.ma5
      },
      {
        name: 'MA20',
        type: 'line',
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: { color: '#909399' },
        lineStyle: { width: 1.5, type: 'solid' },
        showSymbol: false,
        data: stockData.value.ma20
      },
      {
        name: 'MA60',
        type: 'line',
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: { color: '#673ab7' },
        lineStyle: { width: 1.5, type: 'solid' },
        showSymbol: false,
        data: stockData.value.ma60
      },
      // Grid 1: Institutional Net (Stacked)
      {
        name: '外資',
        type: 'bar',
        stack: 'institutional',
        xAxisIndex: 1,
        yAxisIndex: 1,
        itemStyle: { color: '#409EFF' },
        data: stockData.value.foreign_net
      },
      {
        name: '投信',
        type: 'bar',
        stack: 'institutional',
        xAxisIndex: 1,
        yAxisIndex: 1,
        itemStyle: { color: '#E6A23C' },
        data: stockData.value.trust_net
      },
      {
        name: '自營商',
        type: 'bar',
        stack: 'institutional',
        xAxisIndex: 1,
        yAxisIndex: 1,
        itemStyle: { color: '#909399' },
        data: stockData.value.dealer_net
      },
      // Grid 2: RSI
      {
        name: 'RSI',
        type: 'line',
        xAxisIndex: 2,
        yAxisIndex: 2,
        itemStyle: { color: '#bd10e0' },
        showSymbol: false,
        data: stockData.value.rsi
      },
      // Grid 3: MACD
      {
        name: 'MACD',
        type: 'line',
        xAxisIndex: 3,
        yAxisIndex: 3,
        itemStyle: { color: '#000000' },
        showSymbol: false,
        data: stockData.value.macd
      },
      {
        name: 'Signal',
        type: 'line',
        xAxisIndex: 3,
        yAxisIndex: 3,
        itemStyle: { color: '#E6A23C' },
        showSymbol: false,
        data: stockData.value.macd_signal
      },
      {
        name: 'MACD柱',
        type: 'bar',
        xAxisIndex: 3,
        yAxisIndex: 3,
        itemStyle: {
          color: function(params) {
            return params.value > 0 ? '#f56c6c' : '#67c23a';
          }
        },
        data: stockData.value.macd_hist
      }
    ]
  }
})

const fetchData = async () => {
  if (!stockId.value) return
  loading.value = true
  try {
    const { data } = await axios.get(`http://127.0.0.1:8000/api/stock/${stockId.value}`)
    if (data.error) {
      alert("找不到該檔股票資料")
    } else {
      stockData.value = data
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.data-card {
  text-align: center;
  padding: 15px 0;
}
.data-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}
.data-value {
  font-size: 28px;
  font-weight: bold;
}
.text-up { color: #f56c6c; }
.text-down { color: #67c23a; }
.chart-container {
  height: 800px;
}
.chart {
  height: 100%;
  width: 100%;
}
</style>
