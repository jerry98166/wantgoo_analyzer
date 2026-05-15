<template>
  <div class="watchlist-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <h2>自選股清單</h2>
          <div class="header-actions">
            <el-input 
              v-model="newStockId" 
              placeholder="輸入股票代號 (如 2330)" 
              style="width: 200px; margin-right: 10px;"
            />
            <el-input 
              v-model="newStockName" 
              placeholder="輸入股票名稱 (如 台積電)" 
              style="width: 200px; margin-right: 10px;"
            />
            <el-button type="primary" @click="addStock">加入自選</el-button>
          </div>
        </div>
      </template>
      
      <el-table 
        v-loading="loading" 
        :data="watchlist" 
        style="width: 100%"
        :row-class-name="tableRowClassName"
      >
        <el-table-column prop="stock_id" label="代號" width="100" />
        <el-table-column prop="stock_name" label="名稱" width="150" />
        <el-table-column label="最新收盤價" width="150">
          <template #default="scope">
            {{ scope.row.close ? scope.row.close.toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="漲跌幅 (%)" width="150">
          <template #default="scope">
            <span v-if="scope.row.change_pct !== null" :class="scope.row.change_pct > 0 ? 'up' : (scope.row.change_pct < 0 ? 'down' : '')">
              {{ scope.row.change_pct > 0 ? '+' : '' }}{{ scope.row.change_pct.toFixed(2) }}%
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="成交量 (張)" width="150">
          <template #default="scope">
            {{ scope.row.volume ? Math.round(scope.row.volume) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" type="danger" @click="removeStock(scope.row.stock_id)">刪除</el-button>
            <el-button size="small" @click="viewDetail(scope.row.stock_id)">詳細</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 警示設定 (簡易版) -->
    <el-card class="box-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <h2>股價警示設定</h2>
        </div>
      </template>
      <el-alert title="功能建置中：警示功能將於下一階段開放" type="info" :closable="false" show-icon />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api' // Assuming api.js exists in src

const watchlist = ref([])
const loading = ref(false)
const newStockId = ref('')
const newStockName = ref('')

const fetchWatchlist = async () => {
  loading.value = true
  try {
    const response = await api.get('/api/watchlist')
    watchlist.value = response.data
  } catch (error) {
    ElMessage.error('無法載入自選股清單')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const addStock = async () => {
  if (!newStockId.value || !newStockName.value) {
    ElMessage.warning('請輸入股票代號與名稱')
    return
  }
  
  try {
    await api.post('/api/watchlist', {
      stock_id: newStockId.value,
      stock_name: newStockName.value
    })
    ElMessage.success('加入成功')
    newStockId.value = ''
    newStockName.value = ''
    fetchWatchlist()
  } catch (error) {
    if (error.response && error.response.status === 400) {
      ElMessage.warning('該股票已在自選清單中')
    } else {
      ElMessage.error('加入失敗')
    }
  }
}

const removeStock = async (stockId) => {
  try {
    await api.delete(`/api/watchlist/${stockId}`)
    ElMessage.success('刪除成功')
    fetchWatchlist()
  } catch (error) {
    ElMessage.error('刪除失敗')
  }
}

const viewDetail = (stockId) => {
  // 透過事件發射給父層 App.vue，或使用 vue-router (目前似乎是用 activeMenu 控制)
  // 因為我們在組件內，可以發送自訂事件或全域 event bus。
  // 這裡先留空或觸發一個自訂事件。
  ElMessage.info('即將切換到個股詳細頁: ' + stockId)
  window.dispatchEvent(new CustomEvent('view-stock', { detail: stockId }))
}

onMounted(() => {
  fetchWatchlist()
})
</script>

<style scoped>
.watchlist-container {
  padding: 10px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-header h2 {
  margin: 0;
  font-size: 18px;
  color: var(--el-text-color-primary);
}
.header-actions {
  display: flex;
}
.up {
  color: #f56c6c;
  font-weight: bold;
}
.down {
  color: #67c23a;
  font-weight: bold;
}
</style>