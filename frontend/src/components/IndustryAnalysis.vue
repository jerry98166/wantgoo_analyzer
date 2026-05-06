<template>
  <div>
    <h2>產業板塊分析：資金板塊輪動與熱力圖</h2>
    <p>觀察資金淨流入（買超）與淨流出（賣超）最多的產業，以及整體市場資金板塊分佈的板塊熱力圖，協助判斷現階段的市場主線板塊。</p>
    
    <el-row :gutter="20" v-loading="loading" style="margin-bottom: 20px;">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span style="font-weight: bold;">🗺️ 台股產業板塊資金熱力圖 (Treemap)</span>
              <span style="font-size: 12px; color: #909399; margin-left: 10px;">區塊大小 = 成交金額占比 | 顏色深淺 = 法人淨買賣超強度</span>
            </div>
          </template>
          <div class="treemap-container">
            <v-chart class="chart" :option="treemapOption" autoresize />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" v-loading="loading">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span style="color: #f56c6c; font-weight: bold;">🔥 資金匯聚（買超前十產業）</span>
            </div>
          </template>
          <div class="chart-container">
            <v-chart class="chart" :option="buyChartOption" autoresize />
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span style="color: #67c23a; font-weight: bold;">🧊 資金撤出（賣超前十產業）</span>
            </div>
          </template>
          <div class="chart-container">
            <v-chart class="chart" :option="sellChartOption" autoresize />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

const loading = ref(false)
const topBuys = ref([])
const topSells = ref([])
const allIndustries = ref([])

const treemapOption = computed(() => {
  // Normalize color based on Total_Net
  const maxAbsNet = Math.max(...allIndustries.value.map(i => Math.abs(i.Total_Net)))
  
  const treemapData = allIndustries.value.map(item => {
    // Red for buy (+), Green for sell (-)
    // Calculate lightness/opacity based on intensity
    const isBuy = item.Total_Net > 0
    const intensity = maxAbsNet ? Math.min(Math.abs(item.Total_Net) / (maxAbsNet * 0.5), 1) : 0
    // Base colors: Red #f56c6c, Green #67c23a
    const baseColor = isBuy ? [245, 108, 108] : [103, 194, 58]
    // Mix with dark grey background to create heat effect
    const color = `rgba(${baseColor[0]}, ${baseColor[1]}, ${baseColor[2]}, ${0.3 + 0.7 * intensity})`
    
    return {
      name: item.Industry,
      value: item.Turnover_Value, // Size represents turnover
      itemStyle: {
        color: color
      },
      net: item.Total_Net // For tooltip
    }
  })

  return {
    tooltip: {
      formatter: function (info) {
        var value = info.value;
        var net = info.data.net;
        var color = net > 0 ? '#f56c6c' : '#67c23a';
        return `
          <div style="font-weight:bold;margin-bottom:5px;">${info.name}</div>
          成交金額(億): ${Math.round(value)}<br>
          法人買賣超(張): <span style="color:${color}">${Math.round(net)}</span>
        `;
      }
    },
    series: [{
      type: 'treemap',
      width: '100%',
      height: '100%',
      roam: false,
      nodeClick: false,
      breadcrumb: { show: false },
      label: {
        show: true,
        formatter: '{b}\n({c}億)',
        fontSize: 14
      },
      itemStyle: {
        borderColor: '#fff',
        borderWidth: 2,
        gapWidth: 2
      },
      data: treemapData
    }]
  }
})

const buyChartOption = computed(() => {
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'value', name: '總買超張數' },
    yAxis: { 
      type: 'category', 
      data: [...topBuys.value].reverse().map(item => item.Industry),
      axisLabel: { interval: 0 }
    },
    series: [
      {
        name: '三大法人買超',
        type: 'bar',
        itemStyle: { color: '#f56c6c' },
        data: [...topBuys.value].reverse().map(item => item.Total_Net)
      }
    ]
  }
})

const sellChartOption = computed(() => {
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'value', name: '總賣超張數' },
    yAxis: { 
      type: 'category', 
      data: topSells.value.map(item => item.Industry),
      axisLabel: { interval: 0 }
    },
    series: [
      {
        name: '三大法人賣超',
        type: 'bar',
        itemStyle: { color: '#67c23a' },
        data: topSells.value.map(item => item.Total_Net)
      }
    ]
  }
})

const fetchData = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('http://127.0.0.1:8000/api/industry-focus')
    topBuys.value = data.top_buy_industries
    topSells.value = data.top_sell_industries
    allIndustries.value = data.all_industries
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.treemap-container {
  height: 400px;
}
.chart-container {
  height: 400px;
}
.chart {
  height: 100%;
  width: 100%;
}
</style>
