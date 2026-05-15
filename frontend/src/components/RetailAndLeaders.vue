<template>
  <div class="retail-and-leaders">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>吸金排行榜 (總成交值前 20 大)</span>
            </div>
          </template>
          <el-table :data="turnoverLeaders" style="width: 100%" max-height="300" v-loading="loading">
            <el-table-column prop="Stock_ID" label="代號" width="80" />
            <el-table-column prop="Stock_Name" label="名稱" width="100" />
            <el-table-column prop="Close" label="股價" />
            <el-table-column prop="Change_Pct" label="漲跌幅 (%)">
              <template #default="scope">
                <span :class="scope.row.Change_Pct > 0 ? 'up' : scope.row.Change_Pct < 0 ? 'down' : ''">
                  {{ scope.row.Change_Pct.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="Turnover_Value" label="成交值估算 (百萬)">
              <template #default="scope">
                {{ formatNumber(scope.row.Turnover_Value) }}
              </template>
            </el-table-column>
            <el-table-column prop="Total_Net" label="法人買賣超 (張)">
              <template #default="scope">
                <span :class="scope.row.Total_Net > 0 ? 'up' : scope.row.Total_Net < 0 ? 'down' : ''">
                  {{ formatNumber(scope.row.Total_Net) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>散戶被洗出場 (融資大減 + 法人大買)</span>
            </div>
          </template>
          <el-table :data="washedOutList" style="width: 100%" max-height="300" v-loading="loading">
            <el-table-column prop="Stock_Name" label="名稱" width="100" />
            <el-table-column prop="Change_Pct" label="漲跌幅 (%)">
              <template #default="scope">
                <span :class="scope.row.Change_Pct > 0 ? 'up' : scope.row.Change_Pct < 0 ? 'down' : ''">
                  {{ scope.row.Change_Pct.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="Margin_Net" label="融資增減">
              <template #default="scope">
                <span class="down">{{ formatNumber(scope.row.Margin_Net) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="Total_Net" label="法人買賣超">
              <template #default="scope">
                <span class="up">{{ formatNumber(scope.row.Total_Net) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>散戶接滿手血 (融資大增 + 法人大賣)</span>
            </div>
          </template>
          <el-table :data="catchingKnivesList" style="width: 100%" max-height="300" v-loading="loading">
            <el-table-column prop="Stock_Name" label="名稱" width="100" />
            <el-table-column prop="Change_Pct" label="漲跌幅 (%)">
              <template #default="scope">
                <span :class="scope.row.Change_Pct > 0 ? 'up' : scope.row.Change_Pct < 0 ? 'down' : ''">
                  {{ scope.row.Change_Pct.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="Margin_Net" label="融資增減">
              <template #default="scope">
                <span class="up">{{ formatNumber(scope.row.Margin_Net) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="Total_Net" label="法人買賣超">
              <template #default="scope">
                <span class="down">{{ formatNumber(scope.row.Total_Net) }}</span>
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
import { apiClient } from '../api'

const turnoverLeaders = ref([])
const washedOutList = ref([])
const catchingKnivesList = ref([])
const loading = ref(true)

const formatNumber = (num) => {
  return Number(num).toLocaleString(undefined, { maximumFractionDigits: 0 })
}

const fetchRetailAndLeaders = async () => {
  try {
    const { data } = await apiClient.get('/api/retail-and-leaders')
    if (data.error) return
    turnoverLeaders.value = data.turnover_leaders
    washedOutList.value = data.washed_out
    catchingKnivesList.value = data.catching_knives
  } catch (error) {
    console.error('Failed to fetch retail and leaders', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchRetailAndLeaders()
})
</script>

<style scoped>
.card-header { font-weight: bold; }
.up { color: #f56c6c; }
.down { color: #67c23a; }
</style>
