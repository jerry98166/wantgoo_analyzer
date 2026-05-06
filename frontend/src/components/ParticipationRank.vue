<template>
  <div>
    <h2>法人高參與度排行</h2>
    <p>「法人參與率」 = 法人淨買賣超佔當日成交量的比例。這項指標能幫我們找出「法人對股價具備絕對控盤力」的個股。若參與率極高，代表行情的延續性較有保障。</p>
    
    <el-row :gutter="20" v-loading="loading">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span style="color: #f56c6c;">🚀 高控盤買進 (Top 15)</span>
            </div>
          </template>
          <el-table :data="highBuy" style="width: 100%" height="450">
            <el-table-column prop="Stock_Name" label="名稱" width="100" />
            <el-table-column prop="Buy_Participation" label="參與率(%)" width="100">
              <template #default="scope">
                <span style="color: #f56c6c; font-weight: bold;">
                  {{ scope.row.Buy_Participation.toFixed(1) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="Change_Pct" label="漲跌幅" width="80">
              <template #default="scope">
                <span :style="{ color: scope.row.Change_Pct > 0 ? '#f56c6c' : '#67c23a' }">
                  {{ scope.row.Change_Pct > 0 ? '+' : '' }}{{ scope.row.Change_Pct.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="Volume" label="成交量">
              <template #default="scope">
                {{ Math.round(scope.row.Volume) }} 張
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span style="color: #67c23a;">📉 高控盤賣出 (Top 15)</span>
            </div>
          </template>
          <el-table :data="highSell" style="width: 100%" height="450">
            <el-table-column prop="Stock_Name" label="名稱" width="100" />
            <el-table-column prop="Sell_Participation" label="參與率(%)" width="100">
              <template #default="scope">
                <span style="color: #67c23a; font-weight: bold;">
                  {{ scope.row.Sell_Participation.toFixed(1) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="Change_Pct" label="漲跌幅" width="80">
              <template #default="scope">
                <span :style="{ color: scope.row.Change_Pct > 0 ? '#f56c6c' : '#67c23a' }">
                  {{ scope.row.Change_Pct > 0 ? '+' : '' }}{{ scope.row.Change_Pct.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="Volume" label="成交量">
              <template #default="scope">
                {{ Math.round(scope.row.Volume) }} 張
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const loading = ref(false)
const highBuy = ref([])
const highSell = ref([])

const fetchData = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('http://127.0.0.1:8000/api/participation')
    highBuy.value = data.high_buy
    highSell.value = data.high_sell
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
