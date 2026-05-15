<template>
  <div class="institutional-tracking">
    <!-- 1. 總覽 -->
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Aim /></el-icon>
              <span>三大法人總計買賣超 (張)</span>
            </div>
          </template>
          <div class="overview-grid" v-if="trackingData">
            <div class="stat-box">
              <div class="label">外資</div>
              <div :class="['value', trackingData.market_institutional.foreign > 0 ? 'up' : 'down']">
                {{ formatNumber(trackingData.market_institutional.foreign) }}
              </div>
            </div>
            <div class="stat-box">
              <div class="label">投信</div>
              <div :class="['value', trackingData.market_institutional.trust > 0 ? 'up' : 'down']">
                {{ formatNumber(trackingData.market_institutional.trust) }}
              </div>
            </div>
            <div class="stat-box">
              <div class="label">自營商</div>
              <div :class="['value', trackingData.market_institutional.dealer > 0 ? 'up' : 'down']">
                {{ formatNumber(trackingData.market_institutional.dealer) }}
              </div>
            </div>
            <div class="stat-box">
              <div class="label">三大法人合計</div>
              <div :class="['value', trackingData.market_institutional.net > 0 ? 'up' : 'down']">
                {{ formatNumber(trackingData.market_institutional.net) }}
              </div>
            </div>
          </div>
          <div v-else>Loading...</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 2. 圖表分析區 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 土洋產業偏好對比 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><PieChart /></el-icon>
              <span>土洋產業偏好對比 (外資 vs 投信)</span>
              <el-tooltip content="長條圖顯示外資與投信目前重金佈局(或撤出)的前幾大產業，單位為億元。可一眼看出雙方看好或看壞的板塊是否有共識。" placement="top">
                <el-icon class="help-icon"><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
          </template>
          <div style="height: 350px;">
            <v-chart v-if="industryCompareOption" :option="industryCompareOption" autoresize />
            <div v-else style="text-align:center; padding-top: 50px;">載入中...</div>
          </div>
        </el-card>
      </el-col>

      <!-- 法人參與度氣泡圖 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Histogram /></el-icon>
              <span>法人高參與度洞察 (氣泡圖)</span>
              <el-tooltip content="氣泡大小代表「法人參與率」(法人買賣超佔總成交量的比例)。氣泡越大且越靠上方，代表該股目前完全由法人資金主導漲跌。" placement="top">
                <el-icon class="help-icon"><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
          </template>
          <div style="height: 350px;">
            <v-chart v-if="participationOption" :option="participationOption" autoresize />
            <div v-else style="text-align:center; padding-top: 50px;">載入中...</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 3. 名單區 (土洋對作榜) -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Switch /></el-icon>
              <span>土洋對作激烈榜 (外資與投信反向操作)</span>
              <el-tooltip content="列出外資與投信在同一檔股票上發生嚴重分歧的標的。通常當其中一方認輸回補時，會引發強烈的追價或殺跌行情。" placement="top">
                <el-icon class="help-icon"><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
          </template>
          <el-table :data="divergenceList" style="width: 100%" max-height="300">
            <el-table-column prop="Stock_ID" label="代號" width="80" />
            <el-table-column prop="Stock_Name" label="名稱" width="100" />
            <el-table-column prop="Change_Pct" label="漲跌幅 (%)">
              <template #default="scope">
                <span :class="scope.row.Change_Pct > 0 ? 'up' : 'down'">{{ scope.row.Change_Pct.toFixed(2) }}%</span>
              </template>
            </el-table-column>
            <el-table-column prop="Foreign_Net" label="外資買賣超">
              <template #default="scope">
                <span :class="scope.row.Foreign_Net > 0 ? 'up' : 'down'">{{ formatNumber(scope.row.Foreign_Net) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="Trust_Net" label="投信買賣超">
              <template #default="scope">
                <span :class="scope.row.Trust_Net > 0 ? 'up' : 'down'">{{ formatNumber(scope.row.Trust_Net) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="Total_Net" label="法人合計">
              <template #default="scope">
                <span :class="scope.row.Total_Net > 0 ? 'up' : 'down'">{{ formatNumber(scope.row.Total_Net) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 4. 名單區 (土洋同步) -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>土洋同步作多 (外資投信齊買)</span>
            </div>
          </template>
          <el-table :data="syncBuyList" style="width: 100%" max-height="300">
            <el-table-column prop="Stock_ID" label="代號" width="80" />
            <el-table-column prop="Stock_Name" label="名稱" width="100" />
            <el-table-column prop="Close" label="股價" />
            <el-table-column prop="Total_Net" label="法人合計買超">
              <template #default="scope">
                <span class="up">{{ formatNumber(scope.row.Total_Net) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>土洋同步作空 (外資投信齊賣)</span>
            </div>
          </template>
          <el-table :data="syncSellList" style="width: 100%" max-height="300">
            <el-table-column prop="Stock_ID" label="代號" width="80" />
            <el-table-column prop="Stock_Name" label="名稱" width="100" />
            <el-table-column prop="Close" label="股價" />
            <el-table-column prop="Total_Net" label="法人合計賣超">
              <template #default="scope">
                <span class="down">{{ formatNumber(scope.row.Total_Net) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

const trackingData = ref(null)
const syncBuyList = ref([])
const syncSellList = ref([])
const divergenceList = ref([])
const industryCompare = ref([])
const participationBubbles = ref([])

const formatNumber = (num) => {
  return Number(num).toLocaleString(undefined, { maximumFractionDigits: 0 })
}

const fetchTracking = async () => {
  try {
    const { data } = await axios.get('http://127.0.0.1:8000/api/institutional-tracking')
    if (data.error) {
       console.log("Tracking data not ready yet")
       return
    }
    trackingData.value = data
    syncBuyList.value = data.sync_buy || []
    syncSellList.value = data.sync_sell || []
    divergenceList.value = data.divergence_list || []
    industryCompare.value = data.industry_compare || []
    participationBubbles.value = data.participation_bubbles || []
  } catch (error) {
    console.error('Failed to fetch institutional tracking', error)
  }
}

// 產業比較長條圖 (外資 vs 投信)
const industryCompareOption = computed(() => {
  if (!industryCompare.value.length) return null
  
  const industries = industryCompare.value.map(i => i.Industry)
  const foreignData = industryCompare.value.map(i => i.Foreign_Net_Val)
  const trustData = industryCompare.value.map(i => i.Trust_Net_Val)

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: { data: ['外資 (億元)', '投信 (億元)'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: industries, inverse: true },
    series: [
      {
        name: '外資 (億元)',
        type: 'bar',
        data: foreignData,
        itemStyle: { color: '#409eff' }
      },
      {
        name: '投信 (億元)',
        type: 'bar',
        data: trustData,
        itemStyle: { color: '#e6a23c' }
      }
    ]
  }
})

// 法人參與度氣泡圖
const participationOption = computed(() => {
  if (!participationBubbles.value.length) return null
  
  const mappedData = participationBubbles.value.map(item => [
    item.Change_Pct,       // x 軸
    item.Total_Net,        // y 軸
    item.Participation,    // 氣泡大小
    item.Stock_Name,
    item.Stock_ID
  ])

  return {
    tooltip: {
      trigger: 'item',
      formatter: function (params) {
        return `${params.data[3]} (${params.data[4]})<br/>
                漲跌幅: ${params.data[0].toFixed(2)}%<br/>
                買賣超: ${formatNumber(params.data[1])} 張<br/>
                參與度: ${params.data[2].toFixed(1)}%`
      }
    },
    xAxis: {
      type: 'value',
      name: '漲跌幅 (%)',
      splitLine: { lineStyle: { type: 'dashed' } }
    },
    yAxis: {
      type: 'value',
      name: '法人買賣超 (張)',
      splitLine: { lineStyle: { type: 'dashed' } }
    },
    series: [
      {
        name: '個股',
        type: 'scatter',
        data: mappedData,
        symbolSize: function (data) {
          // 將參與度放大以適合氣泡顯示 (限制在 5 ~ 40 之間)
          return Math.max(5, Math.min(40, data[2] * 0.8))
        },
        itemStyle: {
          color: function(params) {
            return params.data[1] > 0 ? '#f56c6c' : '#67c23a'
          },
          opacity: 0.6
        }
      }
    ]
  }
})

onMounted(() => {
  fetchTracking()
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
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
}
.help-icon {
  margin-left: 5px;
  cursor: pointer;
  color: var(--el-text-color-secondary);
}
</style>
