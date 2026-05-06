<template>
  <div>
    <h2>Smart Money (聰明錢) 偷偷吃貨掃描</h2>
    <p>「量縮 + 法人高比例買進 + 股價未大漲」是標準的主力吃貨特徵。這份名單掃描了全市場成交量不高（500~8000張），但法人佔比超過 8%，且股價漲跌幅在 2% 以內的「潛力伏兵」。</p>
    
    <el-card shadow="hover" v-loading="loading">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>🔍 偷偷吃貨雷達 (Smart Money Accumulation)</span>
        </div>
      </template>

      <el-table :data="tableData" style="width: 100%" height="550" :default-sort="{ prop: 'Buy_Participation', order: 'descending' }">
        <el-table-column type="index" label="潛力排名" width="100" align="center">
          <template #default="scope">
            <el-tag :type="scope.$index < 3 ? 'warning' : 'info'" effect="dark" round>
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
        <el-table-column prop="Volume" label="成交量(張)" width="150">
          <template #default="scope">
            {{ Math.round(scope.row.Volume) }}
          </template>
        </el-table-column>
        <el-table-column prop="Total_Net" label="法人淨買超(張)" width="150">
          <template #default="scope">
            <span style="color: #f56c6c; font-weight: bold;">
              +{{ Math.round(scope.row.Total_Net) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="Buy_Participation" label="法人參與度(吃貨力道)" sortable>
          <template #default="scope">
            <el-progress :percentage="Number(scope.row.Buy_Participation.toFixed(1))" :color="customColors" />
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

const customColors = [
  { color: '#f56c6c', percentage: 100 }
]

const fetchData = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('http://127.0.0.1:8000/api/smart-money')
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
