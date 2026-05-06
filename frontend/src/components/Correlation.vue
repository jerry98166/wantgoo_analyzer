<template>
  <div>
    <h2>籌碼與股價關聯 (3D氣泡圖)</h2>
    <p>探討法人買賣超力道與股價近期漲跌幅的關聯。特別加入了「成交量」作為氣泡大小，讓您一眼看出誰是帶量大漲的實質強勢股。</p>
    
    <el-card shadow="hover" v-loading="loading">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="metric-box">
            <div class="metric-title">法人買賣超與漲跌幅相關係數</div>
            <div class="metric-value">{{ correlation.toFixed(3) }}</div>
            <div class="metric-desc">接近 1 代表高度正相關</div>
          </div>
        </el-col>
        <el-col :span="18">
          <div class="chart-container">
            <v-chart class="chart" :option="scatterOption" autoresize />
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

const loading = ref(false)
const correlation = ref(0)
const scatterData = ref([])

const scatterOption = computed(() => {
  return {
    title: { 
      text: '法人買賣超 vs 股價漲跌幅',
      subtext: '氣泡大小 = 成交量',
      left: 'center'
    },
    tooltip: {
      formatter: function (params) {
        return `<b>${params.value[2]}</b><br/>買賣超: ${Math.round(params.value[0])} 張<br/>漲跌幅: ${params.value[1].toFixed(2)} %<br/>成交量: ${Math.round(params.value[3])} 張`
      }
    },
    xAxis: { type: 'value', name: '三大法人買賣超(張)', splitLine: { show: true, lineStyle: { type: 'dashed' } } },
    yAxis: { type: 'value', name: '漲跌幅(%)', splitLine: { show: true, lineStyle: { type: 'dashed' } } },
    series: [
      {
        type: 'scatter',
        symbolSize: function (data) {
          // Normalize volume to bubble size between 8 and 35
          return Math.max(8, Math.min(35, Math.sqrt(data[3]) / 3));
        },
        itemStyle: {
          color: function(params) {
            return params.value[1] > 0 ? '#f56c6c' : '#67c23a';
          },
          opacity: 0.7
        },
        data: scatterData.value.map(item => [
          item.Total_Net, 
          item.Change_Pct, 
          `${item.Stock_ID} ${item.Stock_Name}`,
          item.Volume
        ])
      }
    ]
  }
})

const fetchData = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('http://127.0.0.1:8000/api/correlation')
    correlation.value = data.correlation
    scatterData.value = data.scatter_data
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
.metric-box {
  background: #f4f4f5;
  border-radius: 8px;
  padding: 30px 20px;
  text-align: center;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.metric-title {
  font-size: 16px;
  color: #606266;
  margin-bottom: 15px;
}
.metric-value {
  font-size: 48px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 10px;
}
.metric-desc {
  font-size: 13px;
  color: #909399;
}
.chart-container {
  height: 450px;
}
.chart {
  height: 100%;
  width: 100%;
}
</style>
