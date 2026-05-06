<template>
  <div>
    <h2>大盤多空結構與整體動向</h2>
    <p>分析當日市場漲跌家數與三大法人整體資金流向，快速判斷大盤的多空氛圍與市場廣度（Market Breadth）。</p>
    
    <el-row :gutter="20" v-loading="loading">
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-title">外資淨買賣超</div>
          <div :class="['stat-value', totals.foreign > 0 ? 'up' : 'down']">
            {{ formatLots(totals.foreign) }} 張
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-title">投信淨買賣超</div>
          <div :class="['stat-value', totals.trust > 0 ? 'up' : 'down']">
            {{ formatLots(totals.trust) }} 張
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-title">自營商淨買賣超</div>
          <div :class="['stat-value', totals.dealer > 0 ? 'up' : 'down']">
            {{ formatLots(totals.dealer) }} 張
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;" v-loading="loading">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>三大法人買賣超占比</span>
            </div>
          </template>
          <div class="chart-container">
            <v-chart class="chart" :option="instPieOption" autoresize />
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>大盤漲跌家數結構</span>
            </div>
          </template>
          <div class="chart-container">
            <v-chart class="chart" :option="breadthPieOption" autoresize />
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
const breadth = ref({ up: 0, down: 0, unchanged: 0 })
const totals = ref({ foreign: 0, trust: 0, dealer: 0, net: 0, volume: 0 })

const formatLots = (val) => {
  return new Intl.NumberFormat('en-US').format(Math.round(val))
}

const instPieOption = computed(() => {
  return {
    tooltip: { trigger: 'item' },
    legend: { top: 'bottom' },
    series: [
      {
        name: '買賣超分布',
        type: 'pie',
        radius: '60%',
        data: [
          { value: Math.abs(totals.value.foreign), name: '外資' },
          { value: Math.abs(totals.value.trust), name: '投信' },
          { value: Math.abs(totals.value.dealer), name: '自營商' }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }
})

const breadthPieOption = computed(() => {
  return {
    tooltip: { trigger: 'item' },
    legend: { top: 'bottom' },
    color: ['#f56c6c', '#67c23a', '#909399'], // Red for Up, Green for Down in TW
    series: [
      {
        name: '家數',
        type: 'pie',
        radius: ['40%', '70%'],
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        data: [
          { value: breadth.value.up, name: '上漲家數' },
          { value: breadth.value.down, name: '下跌家數' },
          { value: breadth.value.unchanged, name: '平盤家數' }
        ]
      }
    ]
  }
})

const fetchData = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('http://127.0.0.1:8000/api/market-breadth')
    breadth.value = data.breadth
    totals.value = data.totals
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
.stat-card {
  text-align: center;
  padding: 20px 0;
}
.stat-title {
  font-size: 16px;
  color: #606266;
  margin-bottom: 10px;
}
.stat-value {
  font-size: 32px;
  font-weight: bold;
}
.up { color: #f56c6c; }
.down { color: #67c23a; }
.chart-container {
  height: 300px;
}
.chart {
  height: 100%;
  width: 100%;
}
</style>
