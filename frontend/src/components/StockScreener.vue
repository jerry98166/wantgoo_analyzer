<template>
  <div>
    <h2>AI 籌碼多條件選股器</h2>
    <p>結合了「價格」、「成交量」、「法人籌碼」與「產業別」，自訂您的專屬選股策略，一鍵從全市場中篩選出符合條件的優質標的。</p>
    
    <el-card shadow="never" style="margin-bottom: 20px; background-color: #fbfbfc;">
      <el-form :inline="true" :model="form" class="demo-form-inline">
        <el-form-item label="股價區間">
          <el-input-number v-model="form.priceMin" :min="0" :step="10" placeholder="最低價" />
          <span style="margin: 0 10px;">-</span>
          <el-input-number v-model="form.priceMax" :min="0" :step="10" placeholder="最高價" />
        </el-form-item>
        
        <el-form-item label="法人淨買超(張) >">
          <el-input-number v-model="form.netBuyMin" :step="500" placeholder="大於幾張" />
        </el-form-item>

        <el-form-item label="當日漲幅(%) >">
          <el-input-number v-model="form.changePctMin" :step="1" placeholder="大於幾%" />
        </el-form-item>
        
        <el-form-item label="成交量(張) >">
          <el-input-number v-model="form.volumeMin" :step="1000" placeholder="大於幾張" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="filterData" icon="Search">執行策略篩選</el-button>
          <el-button @click="resetFilter" icon="Refresh">重置</el-button>
          <el-button type="success" @click="exportToCSV" icon="Download" :disabled="filteredData.length === 0">匯出 CSV</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="hover" v-loading="loading">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>符合條件標的共 <strong style="color: #409EFF">{{ filteredData.length }}</strong> 檔</span>
        </div>
      </template>

      <el-table :data="filteredData" style="width: 100%" height="500" :default-sort="{ prop: 'Total_Net', order: 'descending' }">
        <el-table-column prop="Stock_ID" label="代號" width="100" />
        <el-table-column prop="Stock_Name" label="名稱" width="150">
          <template #default="scope">
            <strong>{{ scope.row.Stock_Name }}</strong>
          </template>
        </el-table-column>
        <el-table-column prop="Industry" label="產業別" width="120" />
        <el-table-column prop="Close" label="收盤價" width="100" sortable />
        <el-table-column prop="Change_Pct" label="漲跌幅(%)" width="120" sortable>
          <template #default="scope">
            <span :style="{ color: scope.row.Change_Pct > 0 ? '#f56c6c' : (scope.row.Change_Pct < 0 ? '#67c23a' : '#909399'), fontWeight: 'bold' }">
              {{ scope.row.Change_Pct > 0 ? '+' : '' }}{{ scope.row.Change_Pct.toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="Volume" label="成交量(張)" width="120" sortable>
          <template #default="scope">
            {{ Math.round(scope.row.Volume) }}
          </template>
        </el-table-column>
        <el-table-column prop="Total_Net" label="法人淨買賣(張)" width="150" sortable>
          <template #default="scope">
            <span :style="{ color: scope.row.Total_Net > 0 ? '#f56c6c' : '#67c23a', fontWeight: 'bold' }">
              {{ scope.row.Total_Net > 0 ? '+' : '' }}{{ Math.round(scope.row.Total_Net) }}
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
const allData = ref([])
const filteredData = ref([])

const form = ref({
  priceMin: 0,
  priceMax: 9999,
  netBuyMin: 0,
  changePctMin: 0,
  volumeMin: 0
})

const fetchData = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('http://127.0.0.1:8000/api/all-stocks')
    allData.value = data
    filterData()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const filterData = () => {
  filteredData.value = allData.value.filter(item => {
    return item.Close >= form.value.priceMin &&
           item.Close <= form.value.priceMax &&
           item.Total_Net >= form.value.netBuyMin &&
           item.Change_Pct >= form.value.changePctMin &&
           item.Volume >= form.value.volumeMin
  })
}

const resetFilter = () => {
  form.value = {
    priceMin: 0,
    priceMax: 9999,
    netBuyMin: 0,
    changePctMin: 0,
    volumeMin: 0
  }
  filterData()
}

const exportToCSV = () => {
  if (filteredData.value.length === 0) return;
  const headers = ['代號', '名稱', '產業別', '收盤價', '漲跌幅(%)', '成交量(張)', '法人淨買賣(張)'];
  const rows = filteredData.value.map(row => [
    row.Stock_ID,
    row.Stock_Name,
    row.Industry,
    row.Close,
    row.Change_Pct.toFixed(2),
    Math.round(row.Volume),
    Math.round(row.Total_Net)
  ]);
  
  let csvContent = "data:text/csv;charset=utf-8,\uFEFF" 
                 + headers.join(",") + "\n" 
                 + rows.map(e => e.join(",")).join("\n");
                 
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", "AI_籌碼選股名單.csv");
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

onMounted(() => {
  fetchData()
})
</script>
