<template>
  <div>
    <h2>資金焦點：三大法人買超排行與價格帶分析</h2>
    <p>觀察近期三大法人買超最密集的個股，以及資金主要集中在哪個價格帶。</p>
    
    <el-row :gutter="20" v-loading="loading">
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>三大法人買超前 20 名</span>
            </div>
          </template>
          <div class="chart-container">
            <v-chart class="chart" :option="barChartOption" autoresize />
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>資金價格帶分布</span>
            </div>
          </template>
          <div class="chart-container">
            <v-chart class="chart" :option="pieChartOption" autoresize />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row style="margin-top: 20px;">
      <el-col :span="24">
        <el-card shadow="hover">
          <el-table :data="tableData" style="width: 100%" height="400">
            <el-table-column prop="Stock_ID" label="代號" width="100" />
            <el-table-column prop="Stock_Name" label="名稱" width="120" />
            <el-table-column prop="Close" label="收盤價" width="100" />
            <el-table-column prop="Change_Pct" label="漲跌幅(%)" width="100">
              <template #default="scope">
                <span :style="{ color: scope.row.Change_Pct > 0 ? 'red' : 'green' }">
                  {{ scope.row.Change_Pct.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="Foreign_Net" label="外資(張)" />
            <el-table-column prop="Trust_Net" label="投信(張)" />
            <el-table-column prop="Dealer_Net" label="自營商(張)" />
            <el-table-column prop="Total_Net" label="三大法人總計(張)" />
          </el-table>
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
const priceBands = ref([])

const tableData = computed(() => topBuys.value)

const barChartOption = computed(() => {
  return {
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: topBuys.value.map(item => item.Stock_Name),
      axisLabel: { interval: 0, rotate: 30 }
    },
    yAxis: { type: 'value', name: '買超張數' },
    series: [
      {
        data: topBuys.value.map(item => ({
          value: item.Total_Net,
          itemStyle: { color: item.Change_Pct > 0 ? '#f56c6c' : '#67c23a' } // Red for up, green for down in TW
        })),
        type: 'bar'
      }
    ]
  }
})

const pieChartOption = computed(() => {
  return {
    tooltip: { trigger: 'item' },
    legend: { top: 'bottom' },
    series: [
      {
        name: '價格帶',
        type: 'pie',
        radius: ['40%', '70%'],
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        data: priceBands.value.map(item => ({
          name: item.band,
          value: item.count
        }))
      }
    ]
  }
})

const fetchData = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('http://127.0.0.1:8000/api/top-stocks')
    topBuys.value = data.top_buys
    priceBands.value = data.price_bands
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
.chart-container {
  height: 350px;
}
.chart {
  height: 100%;
  width: 100%;
}
</style>
