<template>
  <div>
    <h2>成交重心人氣王</h2>
    <p>全市場成交量最大的個股排行。高成交量代表市場資金的共識與熱度，再搭配法人買賣超，可看出主力是在「出貨」還是「進貨」。</p>
    
    <el-card shadow="hover" v-loading="loading">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>今日成交量前 20 大個股</span>
        </div>
      </template>

      <el-table :data="tableData" style="width: 100%" height="550" :default-sort="{ prop: 'Volume', order: 'descending' }">
        <el-table-column type="index" label="熱度排名" width="100" align="center">
          <template #default="scope">
            <el-tag :type="scope.$index < 3 ? 'danger' : 'info'" effect="dark" round>
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
            <span :style="{ color: scope.row.Change_Pct > 0 ? '#f56c6c' : '#67c23a', fontWeight: 'bold' }">
              {{ scope.row.Change_Pct > 0 ? '+' : '' }}{{ scope.row.Change_Pct.toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="Volume" label="成交量(張)" width="150" sortable>
          <template #default="scope">
            {{ new Intl.NumberFormat('en-US').format(Math.round(scope.row.Volume)) }}
          </template>
        </el-table-column>
        <el-table-column prop="Total_Net" label="法人淨買賣(張)" width="150">
          <template #default="scope">
            <span :style="{ color: scope.row.Total_Net > 0 ? '#f56c6c' : '#67c23a' }">
              {{ scope.row.Total_Net > 0 ? '+' : '' }}{{ new Intl.NumberFormat('en-US').format(Math.round(scope.row.Total_Net)) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="主力動向解讀">
          <template #default="scope">
            <el-tag v-if="scope.row.Total_Net > 0 && scope.row.Change_Pct > 0" type="danger">爆量推升</el-tag>
            <el-tag v-else-if="scope.row.Total_Net < 0 && scope.row.Change_Pct < 0" type="success">爆量下殺</el-tag>
            <el-tag v-else-if="scope.row.Total_Net < 0 && scope.row.Change_Pct > 0" type="warning">拉高出貨疑慮</el-tag>
            <el-tag v-else-if="scope.row.Total_Net > 0 && scope.row.Change_Pct < 0" type="info">低接買盤</el-tag>
            <el-tag v-else type="info" plain>方向不明</el-tag>
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
    const { data } = await axios.get('http://127.0.0.1:8000/api/volume-leaders')
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
