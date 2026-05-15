<template>
  <div class="smart-money-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>主力籌碼高度集中榜 (Smart Money)</h2>
          <el-tag type="warning">篩選條件：法人買超佔比 > 10% 且 股價未大漲</el-tag>
        </div>
      </template>

      <el-table :data="data" v-loading="loading" style="width: 100%" stripe>
        <el-table-column prop="Stock_ID" label="代號" width="100" />
        <el-table-column prop="Stock_Name" label="名稱" width="120" />
        <el-table-column prop="Close" label="收盤價" width="100" />
        <el-table-column label="漲跌幅" width="100">
          <template #default="scope">
            <span :class="scope.row.Change_Pct > 0 ? 'up' : (scope.row.Change_Pct < 0 ? 'down' : '')">
              {{ scope.row.Change_Pct > 0 ? '+' : '' }}{{ scope.row.Change_Pct.toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="Total_Net" label="法人淨買 (張)" width="120" sortable />
        <el-table-column prop="Chip_Concentration" label="籌碼集中度 (%)" width="150" sortable>
          <template #default="scope">
            <el-progress 
              :percentage="Math.min(100, Math.max(0, scope.row.Chip_Concentration))" 
              :format="(p) => scope.row.Chip_Concentration.toFixed(1) + '%'"
              :status="scope.row.Chip_Concentration > 20 ? 'exception' : (scope.row.Chip_Concentration > 10 ? 'warning' : 'success')"
              :color="customColors"
            />
          </template>
        </el-table-column>
        <el-table-column prop="conviction_score" label="綜合信心評分" width="120" sortable>
          <template #default="scope">
             <el-rate v-model="scope.row.star_score" disabled show-score text-color="#ff9900" :max="5" />
          </template>
        </el-table-column>
        <el-table-column label="操作">
          <template #default="scope">
            <el-button size="small" @click="addToWatchlist(scope.row)">加入自選</el-button>
            <el-button size="small" type="primary" @click="viewDetail(scope.row.Stock_ID)">分析</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const data = ref([])
const loading = ref(false)

const customColors = [
  { color: '#67c23a', percentage: 10 },
  { color: '#e6a23c', percentage: 20 },
  { color: '#f56c6c', percentage: 30 },
]

const fetchData = async () => {
  loading.value = true
  try {
    const res = await api.get('/api/smart-money-advanced')
    data.value = res.data.map(item => ({
      ...item,
      star_score: Math.min(5, (item.conviction_score / 20)) // 將 0-100 分轉為 0-5 星
    }))
  } catch (error) {
    ElMessage.error('資料加載失敗')
  } finally {
    loading.value = false
  }
}

const addToWatchlist = async (row) => {
  try {
    await api.post('/api/watchlist', {
      stock_id: row.Stock_ID,
      stock_name: row.Stock_Name
    })
    ElMessage.success('已加入自選')
  } catch (error) {
    ElMessage.warning('該股票已在清單中或加入失敗')
  }
}

const viewDetail = (stockId) => {
  window.dispatchEvent(new CustomEvent('view-stock', { detail: stockId }))
}

onMounted(fetchData)
</script>

<style scoped>
.smart-money-container {
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