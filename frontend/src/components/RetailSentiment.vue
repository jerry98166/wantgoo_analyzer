<template>
  <div>
    <h2>散戶 vs 法人 (信用交易與籌碼對作)</h2>
    <p>市場上有一句名言：「散戶多空指標」。當散戶瘋狂使用融資買進，但法人卻大舉倒貨時，往往是股價見頂的警訊。反之，當融資大減（散戶停損），法人卻默默吃貨時，通常是絕佳的上車時機。</p>
    
    <el-row :gutter="20" v-loading="loading">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span style="color: #f56c6c; font-weight: bold;">💎 散戶被洗出場 (主力默默吃貨)</span>
              <br><span style="font-size: 12px; color: #909399;">特徵：融資大減 + 法人大買，籌碼流向強者</span>
            </div>
          </template>
          <el-table :data="washedOut" style="width: 100%" height="500">
            <el-table-column prop="Stock_Name" label="名稱" width="100">
              <template #default="scope">
                <strong>{{ scope.row.Stock_Name }}</strong>
              </template>
            </el-table-column>
            <el-table-column prop="Change_Pct" label="漲跌幅" width="80">
              <template #default="scope">
                <span :style="{ color: scope.row.Change_Pct > 0 ? '#f56c6c' : (scope.row.Change_Pct < 0 ? '#67c23a' : '#909399') }">
                  {{ scope.row.Change_Pct > 0 ? '+' : '' }}{{ scope.row.Change_Pct.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="Total_Net" label="法人淨買(張)">
              <template #default="scope">
                <span style="color: #f56c6c; font-weight: bold;">+{{ Math.round(scope.row.Total_Net) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="Margin_Net" label="融資增減(張)">
              <template #default="scope">
                <span style="color: #67c23a; font-weight: bold;">{{ Math.round(scope.row.Margin_Net) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span style="color: #67c23a; font-weight: bold;">🔪 散戶接滿手血 (主力高檔出貨)</span>
              <br><span style="font-size: 12px; color: #909399;">特徵：融資大增 + 法人大賣，籌碼流向弱者</span>
            </div>
          </template>
          <el-table :data="catchingKnives" style="width: 100%" height="500">
            <el-table-column prop="Stock_Name" label="名稱" width="100">
              <template #default="scope">
                <strong>{{ scope.row.Stock_Name }}</strong>
              </template>
            </el-table-column>
            <el-table-column prop="Change_Pct" label="漲跌幅" width="80">
              <template #default="scope">
                <span :style="{ color: scope.row.Change_Pct > 0 ? '#f56c6c' : (scope.row.Change_Pct < 0 ? '#67c23a' : '#909399') }">
                  {{ scope.row.Change_Pct > 0 ? '+' : '' }}{{ scope.row.Change_Pct.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="Total_Net" label="法人淨賣(張)">
              <template #default="scope">
                <span style="color: #67c23a; font-weight: bold;">{{ Math.round(scope.row.Total_Net) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="Margin_Net" label="融資增減(張)">
              <template #default="scope">
                <span style="color: #f56c6c; font-weight: bold;">+{{ Math.round(scope.row.Margin_Net) }}</span>
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
const washedOut = ref([])
const catchingKnives = ref([])

const fetchData = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('http://127.0.0.1:8000/api/retail-sentiment')
    washedOut.value = data.washed_out
    catchingKnives.value = data.catching_knives
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
