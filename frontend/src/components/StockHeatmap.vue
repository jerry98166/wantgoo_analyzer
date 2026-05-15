<template>
  <div class="stock-heatmap">
    <!-- 頂部統計摘要 -->
    <div class="heatmap-header">
      <div class="summary-cards">
        <div class="summary-card up">
          <div class="summary-icon">
            <el-icon :size="22"><Top /></el-icon>
          </div>
          <div class="summary-info">
            <span class="summary-value">{{ summary.up }}</span>
            <span class="summary-label">上漲家數</span>
          </div>
        </div>
        <div class="summary-card down">
          <div class="summary-icon">
            <el-icon :size="22"><Bottom /></el-icon>
          </div>
          <div class="summary-info">
            <span class="summary-value">{{ summary.down }}</span>
            <span class="summary-label">下跌家數</span>
          </div>
        </div>
        <div class="summary-card neutral">
          <div class="summary-icon">
            <el-icon :size="22"><Minus /></el-icon>
          </div>
          <div class="summary-info">
            <span class="summary-value">{{ summary.unchanged }}</span>
            <span class="summary-label">平盤</span>
          </div>
        </div>
        <div class="summary-card" :class="summary.avg_change >= 0 ? 'up' : 'down'">
          <div class="summary-icon">
            <el-icon :size="22"><TrendCharts /></el-icon>
          </div>
          <div class="summary-info">
            <span class="summary-value">{{ summary.avg_change >= 0 ? '+' : '' }}{{ summary.avg_change }}%</span>
            <span class="summary-label">全市場均漲跌</span>
          </div>
        </div>
      </div>
      <div class="heatmap-controls">
        <el-segmented v-model="sizeMode" :options="sizeModeOptions" size="small" />
        <el-tooltip content="方塊大小依據成交值或市值，顏色代表漲跌幅" placement="bottom">
          <el-icon :size="18" style="cursor: help; color: var(--text-regular); margin-left: 8px;"><QuestionFilled /></el-icon>
        </el-tooltip>
      </div>
    </div>

    <!-- 熱力圖主體 -->
    <el-card shadow="hover" class="heatmap-card">
      <template #header>
        <div class="card-header">
          <div class="card-title">
            <el-icon :size="20" color="#409EFC"><Grid /></el-icon>
            <span>台股產業熱力圖</span>
            <el-tag v-if="dateStr" type="info" size="small" effect="plain" style="margin-left: 10px;">
              {{ formattedDate }}
            </el-tag>
          </div>
          <div class="card-actions">
            <el-button-group size="small">
              <el-button :type="showLabels ? 'primary' : ''" @click="showLabels = !showLabels">
                <el-icon><View /></el-icon> 標籤
              </el-button>
              <el-button :type="flatMode ? 'primary' : ''" @click="flatMode = !flatMode">
                <el-icon><Menu /></el-icon> {{ flatMode ? '巢狀' : '攤平' }}
              </el-button>
            </el-button-group>
          </div>
        </div>
      </template>
      <div class="heatmap-container" v-loading="loading">
        <v-chart v-if="heatmapOption" :option="heatmapOption" autoresize @click="handleChartClick" />
        <el-empty v-else-if="!loading" description="暫無熱力圖資料" />
      </div>
    </el-card>

    <!-- 產業排行 & 個股排行 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 產業漲跌排行 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="card-title">
                <el-icon :size="18" color="#E6A23C"><Histogram /></el-icon>
                <span>產業漲跌排行</span>
              </div>
            </div>
          </template>
          <div style="height: 380px;" v-loading="loading">
            <v-chart v-if="industryRankOption" :option="industryRankOption" autoresize />
          </div>
        </el-card>
      </el-col>

      <!-- 成交值 Top 20 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="card-title">
                <el-icon :size="18" color="#F56C6C"><Trophy /></el-icon>
                <span>個股成交值 Top 20</span>
              </div>
            </div>
          </template>
          <div class="top-stocks-list" v-loading="loading">
            <div
              v-for="(stock, idx) in topStocks"
              :key="stock.stock_id"
              class="top-stock-item"
              @click="viewStock(stock.stock_id)"
            >
              <div class="stock-rank" :class="getRankClass(idx)">{{ idx + 1 }}</div>
              <div class="stock-info">
                <span class="stock-name">{{ stock.name }}</span>
                <span class="stock-id">{{ stock.stock_id }}</span>
              </div>
              <div class="stock-price">{{ stock.close }}</div>
              <div class="stock-change" :class="stock.change_pct >= 0 ? 'up' : 'down'">
                {{ stock.change_pct >= 0 ? '+' : '' }}{{ stock.change_pct }}%
              </div>
              <div class="stock-turnover">
                <div class="turnover-bar" :style="{ width: getTurnoverWidth(stock.value) + '%' }"></div>
                <span>{{ formatTurnover(stock.value) }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 色階說明 -->
    <div class="color-legend">
      <div class="legend-label">跌停 -10%</div>
      <div class="legend-gradient"></div>
      <div class="legend-label">漲停 +10%</div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { apiClient } from '../api'

const loading = ref(true)
const heatmapData = ref([])
const summary = ref({ up: 0, down: 0, unchanged: 0, avg_change: 0, total_stocks: 0 })
const dateStr = ref('')
const showLabels = ref(true)
const flatMode = ref(false)
const sizeMode = ref('turnover')
const sizeModeOptions = [
  { label: '依成交值', value: 'turnover' },
  { label: '依股價 × 量', value: 'weighted' },
]

const formattedDate = computed(() => {
  if (!dateStr.value) return ''
  const d = dateStr.value
  return `${d.substring(0, 4)}/${d.substring(4, 6)}/${d.substring(6, 8)}`
})

const fetchHeatmapData = async () => {
  try {
    loading.value = true
    const { data } = await apiClient.get('/api/stock-heatmap')
    if (data.error) {
      console.log('Data not ready:', data.error)
      return
    }
    heatmapData.value = data.industries || []
    summary.value = data.summary || summary.value
    dateStr.value = data.date || ''
  } catch (error) {
    console.error('Failed to fetch heatmap data', error)
  } finally {
    loading.value = false
  }
}

// 色階映射：台灣股市慣例紅漲綠跌
function getColor(changePct) {
  const val = Math.max(-10, Math.min(10, changePct))
  if (val > 0) {
    // 淺紅 -> 深紅
    const intensity = Math.min(val / 10, 1)
    const r = Math.round(220 + 35 * intensity)
    const g = Math.round(160 - 140 * intensity)
    const b = Math.round(150 - 130 * intensity)
    return `rgb(${r}, ${g}, ${b})`
  } else if (val < 0) {
    // 淺綠 -> 深綠
    const intensity = Math.min(Math.abs(val) / 10, 1)
    const r = Math.round(150 - 130 * intensity)
    const g = Math.round(190 + 30 * intensity)
    const b = Math.round(150 - 120 * intensity)
    return `rgb(${r}, ${g}, ${b})`
  }
  return '#555555'
}

// 文字顏色：深色方塊用白字
function getTextColor(changePct) {
  const absVal = Math.abs(changePct)
  return absVal > 2 ? '#ffffff' : '#e0e0e0'
}

const heatmapOption = computed(() => {
  if (!heatmapData.value.length) return null

  const seriesData = flatMode.value
    ? buildFlatData()
    : buildNestedData()

  return {
    tooltip: {
      backgroundColor: 'rgba(20, 20, 20, 0.92)',
      borderColor: 'rgba(255,255,255,0.1)',
      textStyle: { color: '#e0e0e0', fontSize: 13 },
      formatter: function (info) {
        const d = info.data
        if (!d || d._isIndustry) {
          return `<div style="font-weight:bold;font-size:14px;margin-bottom:4px;">${info.name}</div>
                  <span style="color:${d.change_pct >= 0 ? '#ef5350' : '#26a69a'}">均漲跌: ${d.change_pct >= 0 ? '+' : ''}${d.change_pct}%</span>`
        }
        const changeColor = d.change_pct >= 0 ? '#ef5350' : '#26a69a'
        const netColor = d.total_net >= 0 ? '#ef5350' : '#26a69a'
        return `<div style="font-weight:bold;font-size:15px;margin-bottom:6px;">${d.name} (${d.stock_id})</div>
                <div style="display:grid; grid-template-columns: auto auto; gap: 3px 12px; font-size:13px;">
                  <span style="color:#aaa">收盤價</span><span style="font-weight:600">${d.close}</span>
                  <span style="color:#aaa">漲跌幅</span><span style="color:${changeColor};font-weight:600">${d.change_pct >= 0 ? '+' : ''}${d.change_pct}%</span>
                  <span style="color:#aaa">成交值</span><span>${formatTurnover(d.value)}百萬</span>
                  <span style="color:#aaa">法人淨買</span><span style="color:${netColor}">${d.total_net}張</span>
                </div>`
      }
    },
    series: [{
      name: '台股熱力圖',
      type: 'treemap',
      width: '100%',
      height: '100%',
      roam: false,
      nodeClick: false,
      breadcrumb: {
        show: true,
        top: 4,
        left: 10,
        itemStyle: { color: 'rgba(255,255,255,0.08)', borderColor: 'rgba(255,255,255,0.15)' },
        textStyle: { color: '#aaa', fontSize: 12 }
      },
      levels: getLevels(),
      data: seriesData
    }]
  }
})

function getLevels() {
  if (flatMode.value) {
    return [{
      itemStyle: {
        borderColor: 'rgba(0,0,0,0.5)',
        borderWidth: 1,
        gapWidth: 2
      }
    }]
  }
  return [
    {
      // 產業級別
      itemStyle: {
        borderColor: 'rgba(0,0,0,0.7)',
        borderWidth: 3,
        gapWidth: 3
      },
      upperLabel: {
        show: true,
        height: 24,
        color: '#fff',
        fontSize: 13,
        fontWeight: 'bold',
        backgroundColor: 'rgba(0,0,0,0.4)',
        padding: [4, 8],
        formatter: function(params) {
          const d = params.data
          if (d && d.change_pct !== undefined) {
            return `${params.name} ${d.change_pct >= 0 ? '+' : ''}${d.change_pct}%`
          }
          return params.name
        }
      }
    },
    {
      // 個股級別
      itemStyle: {
        borderColor: 'rgba(0,0,0,0.3)',
        borderWidth: 1,
        gapWidth: 1
      },
      label: {
        show: showLabels.value,
        formatter: function (params) {
          const d = params.data
          if (!d || !d.name) return ''
          const pctStr = d.change_pct !== undefined
            ? `${d.change_pct >= 0 ? '+' : ''}${d.change_pct}%`
            : ''
          // 根據方塊大小決定是否顯示完整資訊
          if (params.treeAncestors && params.treeAncestors.length > 0) {
            return `{name|${d.name}}\n{pct|${pctStr}}`
          }
          return `${d.name}\n${pctStr}`
        },
        rich: {
          name: {
            fontSize: 13,
            fontWeight: 'bold',
            color: '#fff',
            lineHeight: 20
          },
          pct: {
            fontSize: 12,
            color: 'rgba(255,255,255,0.85)',
            lineHeight: 18
          }
        }
      }
    }
  ]
}

function buildNestedData() {
  return heatmapData.value.map(industry => ({
    name: industry.name,
    value: industry.value,
    change_pct: industry.change_pct,
    _isIndustry: true,
    itemStyle: {
      color: getColor(industry.change_pct),
    },
    children: industry.children.map(stock => ({
      name: stock.name,
      stock_id: stock.stock_id,
      value: stock.value,
      change_pct: stock.change_pct,
      close: stock.close,
      volume: stock.volume,
      total_net: stock.total_net,
      itemStyle: {
        color: getColor(stock.change_pct),
      },
      label: {
        color: getTextColor(stock.change_pct)
      }
    }))
  }))
}

function buildFlatData() {
  const all = []
  for (const industry of heatmapData.value) {
    for (const stock of industry.children) {
      all.push({
        name: stock.name,
        stock_id: stock.stock_id,
        value: stock.value,
        change_pct: stock.change_pct,
        close: stock.close,
        volume: stock.volume,
        total_net: stock.total_net,
        itemStyle: { color: getColor(stock.change_pct) },
        label: {
          show: showLabels.value,
          color: getTextColor(stock.change_pct),
          formatter: function(params) {
            const d = params.data
            if (!d) return ''
            return `{name|${d.name}}\n{pct|${d.change_pct >= 0 ? '+' : ''}${d.change_pct}%}`
          },
          rich: {
            name: { fontSize: 12, fontWeight: 'bold', color: '#fff', lineHeight: 18 },
            pct: { fontSize: 11, color: 'rgba(255,255,255,0.85)', lineHeight: 16 }
          }
        }
      })
    }
  }
  all.sort((a, b) => b.value - a.value)
  return all
}

// 產業排行條圖
const industryRankOption = computed(() => {
  if (!heatmapData.value.length) return null

  const sorted = [...heatmapData.value]
    .sort((a, b) => b.change_pct - a.change_pct)

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(20, 20, 20, 0.92)',
      borderColor: 'rgba(255,255,255,0.1)',
      textStyle: { color: '#e0e0e0' }
    },
    grid: { left: '3%', right: '8%', bottom: '3%', top: '3%', containLabel: true },
    xAxis: {
      type: 'value',
      name: '均漲跌 %',
      axisLabel: { formatter: '{value}%' },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } }
    },
    yAxis: {
      type: 'category',
      data: sorted.map(i => i.name),
      inverse: true,
      axisLabel: { fontSize: 12 }
    },
    series: [{
      name: '均漲跌幅',
      type: 'bar',
      barMaxWidth: 18,
      data: sorted.map(i => ({
        value: i.change_pct,
        itemStyle: {
          color: getColor(i.change_pct),
          borderRadius: i.change_pct >= 0 ? [0, 4, 4, 0] : [4, 0, 0, 4]
        }
      })),
      label: {
        show: true,
        position: 'right',
        formatter: p => `${p.value >= 0 ? '+' : ''}${p.value}%`,
        fontSize: 11,
        color: '#aaa'
      }
    }]
  }
})

// Top 20 個股
const topStocks = computed(() => {
  if (!heatmapData.value.length) return []
  const all = []
  for (const industry of heatmapData.value) {
    for (const stock of industry.children) {
      all.push(stock)
    }
  }
  return all.sort((a, b) => b.value - a.value).slice(0, 20)
})

const maxTurnover = computed(() => {
  if (!topStocks.value.length) return 1
  return topStocks.value[0].value
})

function getTurnoverWidth(val) {
  return Math.min((val / maxTurnover.value) * 100, 100)
}

function formatTurnover(val) {
  if (val >= 10000) return (val / 10000).toFixed(1) + '萬'
  if (val >= 1000) return (val / 1000).toFixed(1) + 'k'
  return val.toFixed(0)
}

function getRankClass(idx) {
  if (idx === 0) return 'gold'
  if (idx === 1) return 'silver'
  if (idx === 2) return 'bronze'
  return ''
}

function viewStock(stockId) {
  window.dispatchEvent(new CustomEvent('view-stock', { detail: stockId }))
}

function handleChartClick(params) {
  const d = params.data
  if (d && d.stock_id) {
    viewStock(d.stock_id)
  }
}

onMounted(() => {
  fetchHeatmapData()
})
</script>

<style scoped>
.stock-heatmap {
  width: 100%;
}

/* --- Header Summary --- */
.heatmap-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.summary-cards {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  border-radius: 12px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  min-width: 140px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
}

.summary-card.up .summary-icon {
  color: #ef5350;
  background: rgba(239, 83, 80, 0.1);
}

.summary-card.down .summary-icon {
  color: #26a69a;
  background: rgba(38, 166, 154, 0.1);
}

.summary-card.neutral .summary-icon {
  color: #909399;
  background: rgba(144, 147, 153, 0.1);
}

.summary-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.summary-info {
  display: flex;
  flex-direction: column;
}

.summary-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.summary-card.up .summary-value {
  color: #ef5350;
}

.summary-card.down .summary-value {
  color: #26a69a;
}

.summary-label {
  font-size: 12px;
  color: var(--text-regular);
  margin-top: 2px;
}

.heatmap-controls {
  display: flex;
  align-items: center;
}

/* --- Heatmap Card --- */
.heatmap-card {
  border-radius: 16px !important;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  font-size: 16px;
}

.heatmap-container {
  height: 620px;
  background: #1a1a2e;
  border-radius: 12px;
  overflow: hidden;
}

/* --- Top Stocks List --- */
.top-stocks-list {
  max-height: 380px;
  overflow-y: auto;
}

.top-stock-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 1px solid var(--border-color);
}

.top-stock-item:last-child {
  border-bottom: none;
}

.top-stock-item:hover {
  background: rgba(64, 158, 255, 0.06);
  transform: translateX(4px);
}

.stock-rank {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  background: rgba(144, 147, 153, 0.1);
  color: var(--text-regular);
  flex-shrink: 0;
}

.stock-rank.gold {
  background: linear-gradient(135deg, #FFD700, #FFA500);
  color: #fff;
  box-shadow: 0 2px 8px rgba(255, 215, 0, 0.3);
}

.stock-rank.silver {
  background: linear-gradient(135deg, #C0C0C0, #A0A0A0);
  color: #fff;
}

.stock-rank.bronze {
  background: linear-gradient(135deg, #CD7F32, #A0522D);
  color: #fff;
}

.stock-info {
  display: flex;
  flex-direction: column;
  min-width: 80px;
}

.stock-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
}

.stock-id {
  font-size: 11px;
  color: var(--text-regular);
}

.stock-price {
  font-weight: 600;
  font-size: 14px;
  min-width: 65px;
  text-align: right;
  color: var(--text-primary);
}

.stock-change {
  font-weight: 700;
  font-size: 13px;
  min-width: 65px;
  text-align: right;
  padding: 3px 8px;
  border-radius: 6px;
}

.stock-change.up {
  color: #ef5350;
  background: rgba(239, 83, 80, 0.08);
}

.stock-change.down {
  color: #26a69a;
  background: rgba(38, 166, 154, 0.08);
}

.stock-turnover {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
  min-width: 80px;
}

.stock-turnover span {
  position: relative;
  z-index: 1;
  font-size: 12px;
  color: var(--text-regular);
  padding-left: 6px;
}

.turnover-bar {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, rgba(64, 158, 255, 0.15), rgba(64, 158, 255, 0.06));
  transition: width 0.6s ease;
}

/* --- Color Legend --- */
.color-legend {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 20px;
  padding: 10px;
}

.legend-label {
  font-size: 12px;
  color: var(--text-regular);
  font-weight: 600;
}

.legend-gradient {
  width: 320px;
  height: 14px;
  border-radius: 7px;
  background: linear-gradient(to right,
    #006400,
    #26a69a,
    #555555,
    #ef5350,
    #b71c1c
  );
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

/* --- Dark mode adjustments --- */
html.dark .heatmap-container {
  background: #0d0d1a;
}

html.dark .summary-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

html.dark .summary-card:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.35);
}
</style>
