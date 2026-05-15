<template>
  <div class="market-summary">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>大盤指數與總量</span>
            </div>
          </template>
          <div class="overview-grid" v-if="summary">
            <div class="stat-box">
              <div class="label">加權指數</div>
              <div :class="['value', summary.change_pct > 0 ? 'up' : 'down']">
                {{ summary.taiex.toLocaleString() }}
              </div>
            </div>
            <div class="stat-box">
              <div class="label">漲跌點 / 幅度</div>
              <div :class="['value', summary.change_pct > 0 ? 'up' : 'down']">
                {{ summary.change > 0 ? '+' : '' }}{{ summary.change }} 
                ({{ summary.change_pct > 0 ? '+' : '' }}{{ summary.change_pct }}%)
              </div>
            </div>
            <div class="stat-box">
              <div class="label">總成交量 (億股)</div>
              <div class="value">{{ summary.volume.toFixed(2) }}</div>
            </div>
            <div class="stat-box">
              <div class="label">總成交值 (億元)</div>
              <div class="value">{{ summary.turnover.toFixed(2) }}</div>
            </div>
          </div>
          <div v-else>Loading...</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>熱門財經新聞 (鉅亨網/玩股網)</span>
            </div>
          </template>
          <el-table :data="newsList" style="width: 100%" v-loading="loadingNews">
            <el-table-column prop="title" label="標題" min-width="300">
              <template #default="scope">
                <a :href="scope.row.link" target="_blank" class="news-link">
                  {{ scope.row.title }}
                </a>
              </template>
            </el-table-column>
            <el-table-column prop="summary" label="摘要" min-width="500">
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { apiClient } from '../api'

const summary = ref(null)
const newsList = ref([])
const trendData = ref(null)
const loadingNews = ref(true)
const loadingTrend = ref(true)

const fetchSummary = async () => {
  try {
    const { data } = await apiClient.get('/api/market-summary')
    summary.value = data
  } catch (error) {
    console.error('Failed to fetch market summary', error)
  }
}

const fetchTrend = async () => {
  try {
    loadingTrend.value = true
    const { data } = await apiClient.get('/api/market-trend')
    if (!data.error) {
      trendData.value = data
    }
  } catch (error) {
    console.error('Failed to fetch market trend', error)
  } finally {
    loadingTrend.value = false
  }
}

const fetchNews = async () => {
  try {
    loadingNews.value = true
    const { data } = await apiClient.get('/api/news')
    newsList.value = data
  } catch (error) {
    console.error('Failed to fetch news', error)
  } finally {
    loadingNews.value = false
  }
}

const trendOption = computed(() => {
  if (!trendData.value) return null
  
  const d = trendData.value
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['大盤K線', 'MA20', 'MA60', '成交量(億股)'],
      top: 0
    },
    grid: [
      { left: '8%', right: '5%', top: '10%', height: '55%' }, // K線主圖
      { left: '8%', right: '5%', top: '70%', height: '20%' }  // 成交量副圖
    ],
    xAxis: [
      { type: 'category', data: d.dates, gridIndex: 0, axisLine: { onZero: false } },
      { type: 'category', data: d.dates, gridIndex: 1, axisLabel: { show: false }, axisTick: { show: false } }
    ],
    yAxis: [
      { type: 'value', gridIndex: 0, scale: true },
      { type: 'value', gridIndex: 1, name: '成交量(億股)' }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 0, end: 100 },
      { show: true, type: 'slider', xAxisIndex: [0, 1], bottom: '0%' }
    ],
    series: [
      {
        name: '大盤K線',
        type: 'candlestick',
        data: d.kline_data,
        itemStyle: {
          color: '#f56c6c',
          color0: '#67c23a',
          borderColor: '#f56c6c',
          borderColor0: '#67c23a'
        }
      },
      {
        name: 'MA20',
        type: 'line',
        data: d.ma20,
        smooth: true,
        lineStyle: { opacity: 0.5 },
        symbol: 'none'
      },
      {
        name: 'MA60',
        type: 'line',
        data: d.ma60,
        smooth: true,
        lineStyle: { opacity: 0.5 },
        symbol: 'none'
      },
      {
        name: '成交量(億股)',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: d.volumes,
        itemStyle: {
          color: function(params) {
            const k = d.kline_data[params.dataIndex]
            return k[1] > k[0] ? '#f56c6c' : '#67c23a'
          }
        }
      }
    ]
  }
})

onMounted(() => {
  fetchSummary()
  fetchTrend()
  fetchNews()
})
</script>

<style scoped>
.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}
.stat-box {
  background-color: var(--el-fill-color-light);
  padding: 20px;
  border-radius: 8px;
  text-align: center;
}
.label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-bottom: 10px;
}
.value {
  font-size: 24px;
  font-weight: bold;
}
.up { color: #f56c6c; }
.down { color: #67c23a; }
.news-link {
  color: #409eff;
  text-decoration: none;
}
.news-link:hover {
  text-decoration: underline;
}
</style>
