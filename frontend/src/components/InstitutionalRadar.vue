<template>
  <div>
    <h2>特定法人作帳與避雷雷達</h2>
    <p>針對「投信」與「自營商」的特殊屬性進行掃描：投信常有季底結帳/作帳行情，而自營商則常為短線隔日沖客，需提防避雷。</p>
    
    <el-row :gutter="20" v-loading="loading">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span style="color: #E6A23C; font-weight: bold;">📈 投信作帳雷達 (高投信參與度)</span>
            </div>
          </template>
          <el-table :data="trustDressing" style="width: 100%" height="500">
            <el-table-column prop="Stock_Name" label="名稱" width="100">
              <template #default="scope">
                <strong>{{ scope.row.Stock_Name }}</strong>
              </template>
            </el-table-column>
            <el-table-column prop="Trust_Participation" label="投信參與(%)" width="110">
              <template #default="scope">
                <span style="color: #E6A23C; font-weight: bold;">
                  {{ scope.row.Trust_Participation.toFixed(1) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="Change_Pct" label="漲跌幅" width="80">
              <template #default="scope">
                <span :style="{ color: scope.row.Change_Pct > 0 ? '#f56c6c' : (scope.row.Change_Pct < 0 ? '#67c23a' : '#909399') }">
                  {{ scope.row.Change_Pct > 0 ? '+' : '' }}{{ scope.row.Change_Pct.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="Trust_Net" label="投信買超(張)">
              <template #default="scope">
                {{ Math.round(scope.row.Trust_Net) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span style="color: #909399; font-weight: bold;">⚡️ 自營商短線避雷針 (極高自營買盤)</span>
              <br><span style="font-size: 12px; color: #909399;">小心隔日倒貨風險</span>
            </div>
          </template>
          <el-table :data="dealerRisk" style="width: 100%" height="475">
            <el-table-column prop="Stock_Name" label="名稱" width="100">
              <template #default="scope">
                <strong>{{ scope.row.Stock_Name }}</strong>
              </template>
            </el-table-column>
            <el-table-column prop="Dealer_Participation" label="自營參與(%)" width="110">
              <template #default="scope">
                <span style="color: #909399; font-weight: bold;">
                  {{ scope.row.Dealer_Participation.toFixed(1) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="Change_Pct" label="漲跌幅" width="80">
              <template #default="scope">
                <span :style="{ color: scope.row.Change_Pct > 0 ? '#f56c6c' : (scope.row.Change_Pct < 0 ? '#67c23a' : '#909399') }">
                  {{ scope.row.Change_Pct > 0 ? '+' : '' }}{{ scope.row.Change_Pct.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="Dealer_Net" label="自營買超(張)">
              <template #default="scope">
                {{ Math.round(scope.row.Dealer_Net) }}
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
const trustDressing = ref([])
const dealerRisk = ref([])

const fetchData = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('http://127.0.0.1:8000/api/institutional-radar')
    trustDressing.value = data.trust_dressing
    dealerRisk.value = data.dealer_risk
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
