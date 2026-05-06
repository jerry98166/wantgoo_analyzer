<template>
  <div>
    <h2>法人同步與對作分析（土洋動向）</h2>
    <p>分析外資與投信（土洋）的動向一致性。找出雙方共同看好的「土洋齊買」標的，或存在分歧的「土洋對作」標的。</p>
    
    <el-tabs type="border-card" v-loading="loading">
      <el-tab-pane label="🔥 土洋齊買 (同步看多)">
        <el-table :data="syncBuy" style="width: 100%" height="500">
          <el-table-column prop="Stock_ID" label="代號" width="100" />
          <el-table-column prop="Stock_Name" label="名稱" width="120" />
          <el-table-column prop="Close" label="收盤價" width="100" />
          <el-table-column prop="Change_Pct" label="漲跌幅(%)" width="100">
            <template #default="scope">
              <span :style="{ color: scope.row.Change_Pct > 0 ? 'red' : 'green' }">
                {{ scope.row.Change_Pct.toFixed(2) }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="Foreign_Net" label="外資買超(張)" />
          <el-table-column prop="Trust_Net" label="投信買超(張)" />
          <el-table-column prop="Total_Net" label="合計買超(張)" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="🧊 土洋齊賣 (同步看空)">
        <el-table :data="syncSell" style="width: 100%" height="500">
          <el-table-column prop="Stock_ID" label="代號" width="100" />
          <el-table-column prop="Stock_Name" label="名稱" width="120" />
          <el-table-column prop="Close" label="收盤價" width="100" />
          <el-table-column prop="Change_Pct" label="漲跌幅(%)" width="100">
            <template #default="scope">
              <span :style="{ color: scope.row.Change_Pct > 0 ? 'red' : 'green' }">
                {{ scope.row.Change_Pct.toFixed(2) }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="Foreign_Net" label="外資賣超(張)" />
          <el-table-column prop="Trust_Net" label="投信賣超(張)" />
          <el-table-column prop="Total_Net" label="合計賣超(張)" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="⚔️ 土洋對作 (多空分歧)">
        <el-table :data="divergence" style="width: 100%" height="500">
          <el-table-column prop="Stock_ID" label="代號" width="100" />
          <el-table-column prop="Stock_Name" label="名稱" width="120" />
          <el-table-column prop="Close" label="收盤價" width="100" />
          <el-table-column prop="Change_Pct" label="漲跌幅(%)" width="100">
            <template #default="scope">
              <span :style="{ color: scope.row.Change_Pct > 0 ? 'red' : 'green' }">
                {{ scope.row.Change_Pct.toFixed(2) }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="Foreign_Net" label="外資淨額(張)">
            <template #default="scope">
              <span :style="{ color: scope.row.Foreign_Net > 0 ? 'red' : 'green' }">
                {{ Math.round(scope.row.Foreign_Net) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="Trust_Net" label="投信淨額(張)">
            <template #default="scope">
              <span :style="{ color: scope.row.Trust_Net > 0 ? 'red' : 'green' }">
                {{ Math.round(scope.row.Trust_Net) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="對作方向">
            <template #default="scope">
              <el-tag :type="scope.row.Trust_Net > 0 ? 'danger' : 'success'">
                {{ scope.row.Trust_Net > 0 ? '投信買 / 外資賣' : '外資買 / 投信賣' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const loading = ref(false)
const syncBuy = ref([])
const syncSell = ref([])
const divergence = ref([])

const fetchData = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('http://127.0.0.1:8000/api/synchrony')
    syncBuy.value = data.sync_buy
    syncSell.value = data.sync_sell
    divergence.value = data.divergence
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
