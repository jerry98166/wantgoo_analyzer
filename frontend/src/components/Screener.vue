<template>
  <div class="screener-container">
    <el-card class="filter-card">
      <template #header>
        <div class="card-header">
          <h2>多條件選股器</h2>
          <el-button type="primary" icon="Search" @click="handleSearch">執行篩選</el-button>
        </div>
      </template>

      <el-form :model="form" label-width="120px" :inline="true">
        <el-form-item label="最低價格">
          <el-input-number v-model="form.min_price" :min="0" />
        </el-form-item>
        <el-form-item label="最高價格">
          <el-input-number v-model="form.max_price" :min="0" />
        </el-form-item>
        <el-form-item label="最低漲幅 (%)">
          <el-input-number v-model="form.min_change_pct" :step="0.1" />
        </el-form-item>
        <el-form-item label="法人買超 (張)">
          <el-input-number v-model="form.min_total_net" :min="0" />
        </el-form-item>
        <el-form-item label="最低成交值 (百萬)">
          <el-input-number v-model="form.min_turnover_value" :min="0" />
        </el-form-item>
        <el-form-item label="產業別">
          <el-select v-model="form.industry" placeholder="不限" clearable>
            <el-option v-for="ind in industries" :key="ind" :label="ind" :value="ind" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <el-table :data="results" v-loading="loading" style="width: 100%; margin-top: 20px;" stripe>
      <el-table-column prop="Stock_ID" label="代號" width="100" />
      <el-table-column prop="Stock_Name" label="名稱" width="120" />
      <el-table-column prop="Industry" label="產業" width="150" />
      <el-table-column prop="Close" label="收盤價" width="100" />
      <el-table-column label="漲跌幅" width="100">
        <template #default="scope">
          <span :class="scope.row.Change_Pct > 0 ? 'up' : (scope.row.Change_Pct < 0 ? 'down' : '')">
            {{ scope.row.Change_Pct > 0 ? '+' : '' }}{{ scope.row.Change_Pct.toFixed(2) }}%
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="Total_Net" label="法人淨買" width="120" sortable />
      <el-table-column prop="Turnover_Value" label="成交值 (M)" width="120" sortable />
      <el-table-column label="操作">
        <template #default="scope">
          <el-button size="small" @click="viewDetail(scope.row.Stock_ID)">分析</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const loading = ref(false)
const results = ref([])
const form = ref({
  min_price: null,
  max_price: null,
  min_change_pct: null,
  min_total_net: 500,
  min_turnover_value: 100,
  industry: null
})

const industries = [
  "半導體業", "電腦及週邊設備業", "電子零組件業", "光電業", "通信網路業", 
  "金融保險業", "建材營造業", "航運業", "生技醫療業", "電機機械"
]

const handleSearch = async () => {
  loading.value = true
  try {
    const res = await api.post('/api/screener', form.value)
    results.value = res.data
    ElMessage.success(`找到 ${res.data.length} 檔符合條件的股票`)
  } catch (error) {
    ElMessage.error('篩選失敗')
  } finally {
    loading.value = false
  }
}

const viewDetail = (stockId) => {
  window.dispatchEvent(new CustomEvent('view-stock', { detail: stockId }))
}
</script>

<style scoped>
.screener-container {
  padding: 10px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.up { color: #f56c6c; font-weight: bold; }
.down { color: #67c23a; font-weight: bold; }
</style>