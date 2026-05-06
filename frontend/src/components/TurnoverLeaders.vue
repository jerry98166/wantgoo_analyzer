<template>
  <div>
    <h2>資金吸血鬼 (成交值排行)</h2>
    <p>比起單純的「成交量」，「成交金額(值)」更能反映市場真實的資金流向。高價股或許成交張數不多，但吸金能力極強。這裡列出今日全台股「成交金額最大」的前 20 名權值指標股。</p>
    
    <el-card shadow="hover" v-loading="loading">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>💰 今日全市場吸金排行榜</span>
        </div>
      </template>

      <el-table :data="tableData" style="width: 100%" height="550" :default-sort="{ prop: 'Turnover_Value', order: 'descending' }">
        <el-table-column type="index" label="吸金排名" width="100" align="center">
          <template #default="scope">
            <el-tag :type="scope.$index < 5 ? 'danger' : 'info'" effect="dark" round>
              Top {{ scope.$index + 1 }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="Stock_ID" label="代號" width="100" />
        <el-table-column prop="Stock_Name" label="名稱" width="150">
          <template #default="scope">
            <strong>{{ scope.row.Stock_Name }}</strong>
          </template>
        </el-table-column>
        <el-table-column prop="Industry" label="產業別" width="120" />
        <el-table-column prop="Close" label="收盤價" width="100" />
        <el-table-column prop="Change_Pct" label="漲跌幅(%)" width="100">
          <template #default="scope">
            <span :style="{ color: scope.row.Change_Pct > 0 ? '#f56c6c' : (scope.row.Change_Pct < 0 ? '#67c23a' : '#909399'), fontWeight: 'bold' }">
              {{ scope.row.Change_Pct > 0 ? '+' : '' }}{{ scope.row.Change_Pct.toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="Turnover_Value" label="成交金額(億元)" width="150" sortable>
          <template #default="scope">
            <span style="font-weight: bold; color: #E6A23C;">
              {{ new Intl.NumberFormat('en-US').format(Math.round(scope.row.Turnover_Value)) }} 億
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="Volume" label="成交量(張)" width="120">
          <template #default="scope">
            {{ new Intl.NumberFormat('en-US').format(Math.round(scope.row.Volume)) }}
          </template>
        </el-table-column>
        <el-table-column prop="Total_Net" label="法人動向(張)" width="150">
          <template #default="scope">
            <span :style="{ color: scope.row.Total_Net > 0 ? '#f56c6c' : '#67c23a' }">
              {{ scope.row.Total_Net > 0 ? '+' : '' }}{{ new Intl.NumberFormat('en-US').format(Math.round(scope.row.Total_Net)) }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const loading = ref(false)
const tableData = ref([])

const fetchData = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('http://127.0.0.1:8000/api/turnover-leaders')
    tableData.value = data
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
