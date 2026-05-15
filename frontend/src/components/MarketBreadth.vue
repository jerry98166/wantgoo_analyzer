<template>
  <div class="market-breadth">
    <el-row :gutter="20">
      <!-- 大盤多空結構 (圓餅圖) -->
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>大盤多空結構</span>
            </div>
          </template>
          <div style="height: 350px;" v-loading="loading">
            <v-chart v-if="breadthOption" :option="breadthOption" autoresize />
          </div>
        </el-card>
      </el-col>

      <!-- 產業資金流向 (長條圖) -->
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>產業法人資金流向 (億元)</span>
            </div>
          </template>
          <div style="height: 350px;" v-loading="loading">
            <v-chart v-if="industryOption" :option="industryOption" autoresize />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { apiClient } from '../api'

const breadthData = ref([])
const topBuyIndustries = ref([])
const topSellIndustries = ref([])
const loading = ref(true)

const fetchMarketBreadth = async () => {
  try {
    const { data } = await apiClient.get('/api/market-breadth-industry')
    if (data.error) {
      console.log("Data not ready")
      return
    }
    breadthData.value = data.breadth
    topBuyIndustries.value = data.top_buy_industries
    topSellIndustries.value = data.top_sell_industries
  } catch (error) {
    console.error('Failed to fetch market breadth', error)
  } finally {
    loading.value = false
  }
}

const breadthOption = computed(() => {
  if (!breadthData.value.length) return null
  return {
    tooltip: { trigger: 'item' },
    legend: { top: '5%', left: 'center' },
    color: ['#f56c6c', '#67c23a', '#909399'], // 紅, 綠, 灰
    series: [
      {
        name: '家數',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: { show: false, position: 'center' },
        emphasis: {
          label: { show: true, fontSize: 20, fontWeight: 'bold' }
        },
        labelLine: { show: false },
        data: breadthData.value
      }
    ]
  }
})

const industryOption = computed(() => {
  if (!topBuyIndustries.value.length) return null

  // 整理長條圖資料，包含買超與賣超
  const combined = [...topBuyIndustries.value, ...topSellIndustries.value].sort((a, b) => b.Inst_Net_Value - a.Inst_Net_Value)
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'value', name: '法人買賣超 (億元)' },
    yAxis: {
      type: 'category',
      data: combined.map(item => item.Industry),
      inverse: true
    },
    series: [
      {
        name: '淨買賣超',
        type: 'bar',
        data: combined.map(item => ({
          value: item.Inst_Net_Value,
          itemStyle: { color: item.Inst_Net_Value > 0 ? '#f56c6c' : '#67c23a' }
        })),
        label: { show: true, position: 'right' }
      }
    ]
  }
})

const treemapOption = computed(() => {
  if (!industryTreemap.value || industryTreemap.value.length === 0) return null

  return {
    tooltip: {
      formatter: function (info) {
        let value = info.value;
        let change = info.data.change;
        return [
          '<div class="tooltip-title">' + info.name + '</div>',
          '成交值: ' + value + ' 百萬<br>',
          '平均漲跌: ' + change + ' %'
        ].join('');
      }
    },
    visualMap: {
      type: 'continuous',
      min: -5,
      max: 5,
      dimension: 2, // Map to the 'change' property which we will put in index 2 of data
      inRange: {
        color: ['#006400', '#67c23a', '#dddddd', '#f56c6c', '#8b0000'] // 深綠 -> 淺綠 -> 灰 -> 淺紅 -> 深紅
      },
      show: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 10,
      text: ['大漲', '大跌']
    },
    series: [
      {
        name: '產業資金地圖',
        type: 'treemap',
        width: '100%',
        height: '80%',
        roam: false,
        nodeClick: false,
        breadcrumb: { show: false },
        itemStyle: {
          borderColor: '#fff',
          gapWidth: 2
        },
        label: {
          show: true,
          formatter: function (params) {
            return params.name + '\n' + params.data.change + '%';
          },
          fontSize: 14,
          fontWeight: 'bold'
        },
        data: industryTreemap.value.map(item => ({
          name: item.name,
          value: [item.value, item.value, item.change], // [視覺大小, tooltip用大小, 顏色映射用的change]
          change: item.change
        }))
      }
    ]
  }
})

onMounted(() => {
  fetchMarketBreadth()
})
</script>

<style scoped>
.card-header { font-weight: bold; }
</style>