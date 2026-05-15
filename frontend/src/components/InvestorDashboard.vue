<template>
  <div class="investor-dashboard" v-loading="loading">
    <el-alert
      v-if="errorMessage"
      :title="errorMessage"
      type="warning"
      show-icon
      :closable="false"
      class="dashboard-alert"
    />

    <el-row :gutter="20">
      <el-col :xs="24" :lg="8">
        <el-card shadow="hover" class="panel-card">
          <template #header>
            <div class="card-header">
              <el-icon><Odometer /></el-icon>
              <span>市場溫度計</span>
              <el-tag v-if="pulse" :type="regimeTagType" effect="dark">{{ pulse.regime }}</el-tag>
            </div>
          </template>
          <div class="chart chart-gauge">
            <v-chart v-if="gaugeOption" :option="gaugeOption" autoresize />
          </div>
          <div v-if="pulse" class="signal-grid">
            <div v-for="item in pulseTiles" :key="item.label" class="signal-tile">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card shadow="hover" class="panel-card">
          <template #header>
            <div class="card-header">
              <el-icon><Compass /></el-icon>
              <span>資金環境雷達</span>
              <el-tooltip content="從五個維度評估大盤健康度：資金動能(成交量)、法人情緒(買賣超)、散戶籌碼(融資壓力)、價格趨勢(漲跌幅)與市場寬度(上漲家數)。數值越飽滿代表大盤結構越健康。" placement="top">
                <el-icon class="help-icon"><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
          </template>
          <div class="chart chart-radar">
            <v-chart v-if="radarOption" :option="radarOption" autoresize />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card shadow="hover" class="panel-card">
          <template #header>
            <div class="card-header">
              <el-icon><Warning /></el-icon>
              <span>風險快訊</span>
            </div>
          </template>
          <div v-if="pulse" class="risk-list">
            <div class="risk-item danger">
              <span>跌停附近</span>
              <strong>{{ pulse.limit_down_count }}</strong>
            </div>
            <div class="risk-item success">
              <span>漲停附近</span>
              <strong>{{ pulse.limit_up_count }}</strong>
            </div>
            <div class="risk-item">
              <span>成交集中度</span>
              <strong>{{ pulse.top10_turnover_share }}%</strong>
            </div>
            <div class="risk-item">
              <span>資料日期</span>
              <strong>{{ formattedDate }}</strong>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="section-row">
      <el-col :xs="24" :lg="8">
        <el-card shadow="hover" class="panel-card">
          <template #header>
            <div class="card-header">
              <el-icon><DataLine /></el-icon>
              <span>漲跌幅分布</span>
            </div>
          </template>
          <div class="chart chart-mid">
            <v-chart v-if="distributionOption" :option="distributionOption" autoresize />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card shadow="hover" class="panel-card">
          <template #header>
            <div class="card-header">
              <el-icon><PieChart /></el-icon>
              <span>三大法人結構</span>
            </div>
          </template>
          <div class="chart chart-mid">
            <v-chart v-if="institutionalMixOption" :option="institutionalMixOption" autoresize />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card shadow="hover" class="panel-card">
          <template #header>
            <div class="card-header">
              <el-icon><Coin /></el-icon>
              <span>成交集中排行</span>
            </div>
          </template>
          <div class="chart chart-mid">
            <v-chart v-if="turnoverOption" :option="turnoverOption" autoresize />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="section-row">
      <el-col :xs="24" :xl="14">
        <el-card shadow="hover" class="panel-card">
          <template #header>
            <div class="card-header">
              <el-icon><Histogram /></el-icon>
              <span>產業熱力圖</span>
            </div>
          </template>
          <div class="chart chart-heat">
            <v-chart v-if="industryOption" :option="industryOption" autoresize />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :xl="10">
        <el-card shadow="hover" class="panel-card">
          <template #header>
            <div class="card-header">
              <el-icon><Operation /></el-icon>
              <span>融資與法人四象限</span>
            </div>
          </template>
          <div class="chart chart-heat">
            <v-chart v-if="marginQuadrantOption" :option="marginQuadrantOption" autoresize />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="section-row">
      <el-col :xs="24">
        <el-card shadow="hover" class="panel-card">
          <template #header>
            <div class="card-header">
              <el-icon><SwitchFilled /></el-icon>
              <span>產業輪動評分</span>
            </div>
          </template>
          <el-table :data="industryRotation" height="330" style="width: 100%">
            <el-table-column prop="Industry" label="產業" min-width="150" />
            <el-table-column prop="stocks" label="家數" width="80" align="right" />
            <el-table-column prop="avg_change" label="均漲跌" width="110" align="right">
              <template #default="scope">
                <span :class="scope.row.avg_change >= 0 ? 'up' : 'down'">{{ formatPct(scope.row.avg_change) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="net" label="法人淨額" width="130" align="right">
              <template #default="scope">
                <span :class="scope.row.net >= 0 ? 'up' : 'down'">{{ formatNumber(scope.row.net) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="turnover" label="成交值" width="130" align="right">
              <template #default="scope">{{ formatNumber(scope.row.turnover) }}</template>
            </el-table-column>
            <el-table-column prop="margin" label="融資增減" width="130" align="right">
              <template #default="scope">
                <span :class="scope.row.margin >= 0 ? 'up' : 'down'">{{ formatNumber(scope.row.margin) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="section-row">
      <el-col v-for="section in featureSections" :key="section.key" :xs="24" :xl="8">
        <el-card shadow="hover" class="feature-card">
          <template #header>
            <div class="card-header">
              <el-icon><component :is="section.icon" /></el-icon>
              <span>{{ section.title }}</span>
              <el-tag size="small" effect="plain">{{ section.data.length }}</el-tag>
            </div>
          </template>
          <el-table :data="section.data" height="310" style="width: 100%">
            <el-table-column prop="Stock_ID" label="代號" width="74" />
            <el-table-column prop="Stock_Name" label="名稱" min-width="98" show-overflow-tooltip />
            <el-table-column prop="Industry" label="產業" min-width="108" show-overflow-tooltip />
            <el-table-column prop="Change_Pct" label="漲跌" width="82" align="right">
              <template #default="scope">
                <span :class="scope.row.Change_Pct >= 0 ? 'up' : 'down'">{{ formatPct(scope.row.Change_Pct) }}</span>
              </template>
            </el-table-column>
            <el-table-column :prop="section.metricKey" :label="section.metricLabel" width="92" align="right">
              <template #default="scope">
                <span :class="metricClass(scope.row[section.metricKey])">{{ formatNumber(scope.row[section.metricKey]) }}</span>
              </template>
            </el-table-column>
            <el-table-column :prop="section.scoreKey" label="分數" width="74" align="right">
              <template #default="scope">
                <el-tag :type="section.tagType" effect="light">{{ scope.row[section.scoreKey] ?? '-' }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'

const loading = ref(true)
const errorMessage = ref('')
const pulse = ref(null)
const industries = ref([])
const smartMoney = ref([])
const riskWatch = ref([])
const opportunities = ref([])
const changeDistribution = ref([])
const institutionalMix = ref([])
const turnoverConcentration = ref([])
const marginQuadrants = ref([])
const momentumLeaders = ref([])
const defensiveCandidates = ref([])
const sellPressure = ref([])
const trustAccumulation = ref([])
const foreignAccumulation = ref([])
const reboundCandidates = ref([])
const marginShortSqueeze = ref([])
const liquidityLeaders = ref([])
const industryRotation = ref([])

const formatNumber = (num) => Number(num || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })
const formatPct = (num) => `${Number(num || 0) > 0 ? '+' : ''}${Number(num || 0).toFixed(2)}%`
const metricClass = (num) => Number(num || 0) >= 0 ? 'up' : 'down'

const fetchDashboard = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const { data } = await axios.get('http://127.0.0.1:8000/api/investor-dashboard')
    if (data.error) {
      errorMessage.value = '資料尚未準備完成，請稍後再試'
      return
    }
    pulse.value = data.pulse
    industries.value = data.industry_heatmap || []
    smartMoney.value = data.smart_money || []
    riskWatch.value = data.risk_watch || []
    opportunities.value = data.opportunities || []
    changeDistribution.value = data.change_distribution || []
    institutionalMix.value = data.institutional_mix || []
    turnoverConcentration.value = data.turnover_concentration || []
    marginQuadrants.value = data.margin_quadrants || []
    momentumLeaders.value = data.momentum_leaders || []
    defensiveCandidates.value = data.defensive_candidates || []
    sellPressure.value = data.sell_pressure || []
    trustAccumulation.value = data.trust_accumulation || []
    foreignAccumulation.value = data.foreign_accumulation || []
    reboundCandidates.value = data.rebound_candidates || []
    marginShortSqueeze.value = data.margin_short_squeeze || []
    liquidityLeaders.value = data.liquidity_leaders || []
    industryRotation.value = data.industry_rotation || []
  } catch (error) {
    errorMessage.value = '無法取得投資決策資料，請確認後端服務已啟動'
    console.error('Failed to fetch investor dashboard', error)
  } finally {
    loading.value = false
  }
}

const formattedDate = computed(() => {
  if (!pulse.value?.date) return '-'
  const date = String(pulse.value.date)
  return `${date.slice(0, 4)}/${date.slice(4, 6)}/${date.slice(6, 8)}`
})

const pulseTiles = computed(() => {
  if (!pulse.value) return []
  return [
    { label: '上漲家數比', value: `${pulse.value.advance_ratio}%` },
    { label: '法人買超比', value: `${pulse.value.net_buy_ratio}%` },
    { label: '融資壓力', value: `${pulse.value.margin_pressure_ratio}%` },
    { label: '前十成交集中', value: `${pulse.value.top10_turnover_share}%` }
  ]
})

const featureSections = computed(() => [
  { key: 'smart', title: '智慧資金排行', icon: 'Money', data: smartMoney.value, metricKey: 'Total_Net', metricLabel: '法人', scoreKey: 'smart_score', tagType: 'danger' },
  { key: 'opportunity', title: '機會候選清單', icon: 'Star', data: opportunities.value, metricKey: 'Total_Net', metricLabel: '法人', scoreKey: 'opportunity_score', tagType: 'success' },
  { key: 'momentum', title: '強勢動能股', icon: 'TrendCharts', data: momentumLeaders.value, metricKey: 'Turnover_Value', metricLabel: '成交值', scoreKey: 'Change_Pct', tagType: 'danger' },
  { key: 'foreign', title: '外資買盤焦點', icon: 'Avatar', data: foreignAccumulation.value, metricKey: 'Foreign_Net', metricLabel: '外資', scoreKey: 'foreign_score', tagType: 'danger' },
  { key: 'trust', title: '投信布局焦點', icon: 'Medal', data: trustAccumulation.value, metricKey: 'Trust_Net', metricLabel: '投信', scoreKey: 'trust_score', tagType: 'warning' },
  { key: 'rebound', title: '法人承接反轉', icon: 'RefreshRight', data: reboundCandidates.value, metricKey: 'Total_Net', metricLabel: '法人', scoreKey: 'rebound_score', tagType: 'success' },
  { key: 'squeeze', title: '融資減碼強彈', icon: 'Lightning', data: marginShortSqueeze.value, metricKey: 'Margin_Net', metricLabel: '融資', scoreKey: 'squeeze_score', tagType: 'success' },
  { key: 'defense', title: '低波防守候選', icon: 'Umbrella', data: defensiveCandidates.value, metricKey: 'Total_Net', metricLabel: '法人', scoreKey: 'defense_score', tagType: 'info' },
  { key: 'sell', title: '法人賣壓排行', icon: 'BottomRight', data: sellPressure.value, metricKey: 'Total_Net', metricLabel: '法人', scoreKey: 'sell_score', tagType: 'warning' },
  { key: 'risk', title: '風險觀察清單', icon: 'CircleCloseFilled', data: riskWatch.value, metricKey: 'Margin_Net', metricLabel: '融資', scoreKey: 'risk_score', tagType: 'warning' },
  { key: 'liquidity', title: '高流動性標的', icon: 'Rank', data: liquidityLeaders.value, metricKey: 'Turnover_Value', metricLabel: '成交值', scoreKey: 'liquidity_score', tagType: 'info' }
])

const regimeTagType = computed(() => {
  const value = pulse.value?.market_temperature || 0
  if (value >= 65) return 'danger'
  if (value >= 50) return 'success'
  if (value >= 35) return 'warning'
  return 'info'
})

const gaugeOption = computed(() => {
  if (!pulse.value) return null
  return {
    series: [{
      type: 'gauge',
      min: 0,
      max: 100,
      progress: { show: true, width: 14 },
      axisLine: { lineStyle: { width: 14 } },
      axisTick: { show: false },
      splitLine: { length: 8, lineStyle: { width: 1 } },
      axisLabel: { distance: 20 },
      pointer: { width: 5 },
      detail: {
        valueAnimation: true,
        formatter: '{value}',
        fontSize: 34,
        fontWeight: 700,
        color: '#303133'
      },
      data: [{ value: pulse.value.market_temperature, name: 'Market' }]
    }]
  }
})

const radarOption = computed(() => {
  if (!pulse.value?.scores?.length) return null
  return {
    tooltip: {},
    radar: {
      radius: '66%',
      indicator: pulse.value.scores.map(item => ({ name: item.name, max: 100 }))
    },
    series: [{
      type: 'radar',
      areaStyle: { opacity: 0.18 },
      lineStyle: { width: 3 },
      data: [{ value: pulse.value.scores.map(item => item.value), name: '環境分數' }]
    }]
  }
})

const distributionOption = computed(() => {
  if (!changeDistribution.value.length) return null
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 36, right: 16, top: 20, bottom: 55 },
    xAxis: {
      type: 'category',
      data: changeDistribution.value.map(item => item.range),
      axisLabel: { rotate: 30 }
    },
    yAxis: { type: 'value', name: '家數' },
    series: [{
      type: 'bar',
      data: changeDistribution.value.map(item => ({
        value: item.count,
        itemStyle: { color: item.range.includes('-') || item.range.includes('<') ? '#67c23a' : '#f56c6c' }
      }))
    }]
  }
})

const institutionalMixOption = computed(() => {
  if (!institutionalMix.value.length) return null
  return {
    tooltip: {
      trigger: 'item',
      formatter: (params) => `${params.data.name}<br/>淨買賣超: ${formatNumber(params.data.net)} 張`
    },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['42%', '68%'],
      data: institutionalMix.value.map(item => ({
        name: item.name,
        value: Math.abs(Number(item.value || 0)),
        net: item.value
      }))
    }]
  }
})

const turnoverOption = computed(() => {
  if (!turnoverConcentration.value.length) return null
  const rows = [...turnoverConcentration.value].reverse()
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const row = rows[params[0].dataIndex]
        return `${row.Stock_Name} (${row.Stock_ID})<br/>成交值: ${formatNumber(row.Turnover_Value)} 百萬<br/>漲跌: ${formatPct(row.Change_Pct)}`
      }
    },
    grid: { left: 78, right: 20, top: 15, bottom: 20 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: rows.map(item => item.Stock_Name) },
    series: [{
      type: 'bar',
      data: rows.map(item => ({
        value: item.Turnover_Value,
        itemStyle: { color: item.Change_Pct >= 0 ? '#f56c6c' : '#67c23a' }
      }))
    }]
  }
})

const industryOption = computed(() => {
  if (!industries.value.length) return null
  const data = industries.value.map((item, index) => [
    index,
    Number(item.avg_change || 0),
    Number(item.heat_score || 0),
    item.Industry,
    Number(item.net || 0),
    Number(item.turnover || 0)
  ])
  return {
    tooltip: {
      formatter: (params) => {
        const row = params.data
        return `${row[3]}<br/>熱度: ${row[2]}<br/>均漲跌: ${row[1].toFixed(2)}%<br/>法人: ${formatNumber(row[4])} 張<br/>成交值: ${formatNumber(row[5])} 百萬`
      }
    },
    grid: { left: 50, right: 25, top: 20, bottom: 95 },
    xAxis: {
      type: 'category',
      data: industries.value.map(item => item.Industry),
      axisLabel: { interval: 0, rotate: 40 }
    },
    yAxis: { type: 'value', name: '均漲跌幅' },
    visualMap: {
      min: 0,
      max: 100,
      dimension: 2,
      orient: 'horizontal',
      left: 'center',
      bottom: 10,
      inRange: { color: ['#67c23a', '#e6a23c', '#f56c6c'] }
    },
    series: [{
      name: '產業熱度',
      type: 'scatter',
      symbolSize: (value) => Math.max(14, Math.min(58, value[2] * 0.62)),
      data
    }]
  }
})

const marginQuadrantOption = computed(() => {
  if (!marginQuadrants.value.length) return null
  return {
    tooltip: {
      formatter: (params) => {
        const row = params.data
        return `${row[3]} (${row[4]})<br/>法人: ${formatNumber(row[0])} 張<br/>融資: ${formatNumber(row[1])} 張<br/>漲跌: ${formatPct(row[2])}`
      }
    },
    grid: { left: 62, right: 24, top: 24, bottom: 52 },
    xAxis: {
      type: 'value',
      name: '法人買賣超',
      splitLine: { lineStyle: { type: 'dashed' } }
    },
    yAxis: {
      type: 'value',
      name: '融資增減',
      splitLine: { lineStyle: { type: 'dashed' } }
    },
    series: [{
      type: 'scatter',
      data: marginQuadrants.value.map(item => [
        item.Total_Net,
        item.Margin_Net,
        item.Change_Pct,
        item.Stock_Name,
        item.Stock_ID,
        item.Turnover_Value
      ]),
      symbolSize: (value) => Math.max(6, Math.min(28, Math.sqrt(Math.abs(value[5] || 0)) / 12)),
      itemStyle: {
        opacity: 0.72,
        color: (params) => params.data[2] >= 0 ? '#f56c6c' : '#67c23a'
      }
    }]
  }
})

onMounted(fetchDashboard)
</script>

<style scoped>
.dashboard-alert {
  margin-bottom: 18px;
}
.section-row {
  margin-top: 20px;
}
.panel-card,
.feature-card {
  height: 100%;
}
.feature-card {
  margin-bottom: 20px;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
}
.card-header .el-tag {
  margin-left: auto;
}
.chart {
  width: 100%;
}
.chart-gauge,
.chart-radar {
  height: 250px;
}
.chart-mid {
  height: 320px;
}
.chart-heat {
  height: 430px;
}
.signal-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.signal-tile,
.risk-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 42px;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--el-fill-color-light);
}
.signal-tile span,
.risk-item span {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.signal-tile strong,
.risk-item strong {
  color: var(--text-primary);
  font-size: 16px;
}
.risk-list {
  display: grid;
  gap: 12px;
}
.risk-item.danger strong,
.up {
  color: #f56c6c;
}
.risk-item.success strong,
.down {
  color: #67c23a;
}
@media (max-width: 900px) {
  .section-row {
    margin-top: 0;
  }
  .panel-card {
    margin-bottom: 18px;
  }
}
</style>
