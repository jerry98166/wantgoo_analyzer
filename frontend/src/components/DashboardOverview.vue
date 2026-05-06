<template>
  <div class="dashboard-wrapper">
    <div class="welcome-header">
      <h2>戰情室儀表板 (Dashboard)</h2>
      <p>一目了然今日台股籌碼動向與盤勢多空，快速掌握關鍵指標。</p>
    </div>

    <el-row :gutter="20" v-loading="loading">
      <!-- Top Left: Market Breadth Mini -->
      <el-col :span="8">
        <el-card shadow="hover" class="dash-card">
          <div class="card-title">今日大盤多空氛圍</div>
          <div class="breadth-content" v-if="breadth">
            <div class="stat-item up">
              <span>上漲家數</span>
              <strong>{{ breadth.up }}</strong>
            </div>
            <div class="stat-item down">
              <span>下跌家數</span>
              <strong>{{ breadth.down }}</strong>
            </div>
          </div>
          <div class="card-footer">
            <el-tag :type="breadth && breadth.up > breadth.down ? 'danger' : 'success'">
              {{ breadth && breadth.up > breadth.down ? '多方勝出' : '空方勝出' }}
            </el-tag>
          </div>
        </el-card>
      </el-col>

      <!-- Top Center: Net Institutional Action -->
      <el-col :span="8">
        <el-card shadow="hover" class="dash-card">
          <div class="card-title">三大法人今日總動向</div>
          <div class="net-content" v-if="totals">
            <div :class="['net-value', totals.net > 0 ? 'up' : 'down']">
              {{ totals.net > 0 ? '+' : '' }}{{ new Intl.NumberFormat('en-US').format(Math.round(totals.net)) }} 張
            </div>
            <div class="sub-net">
              <span style="color:#909399">外資: {{ Math.round(totals.foreign) }}</span> | 
              <span style="color:#909399">投信: {{ Math.round(totals.trust) }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- Top Right: Market Hot News -->
      <el-col :span="8">
        <el-card shadow="hover" class="dash-card news-card">
          <div class="card-title">玩股網最新熱點</div>
          <ul class="news-list" v-if="news.length">
            <li v-for="(item, idx) in news.slice(0, 3)" :key="idx">
              <a :href="item.link" target="_blank">{{ item.title }}</a>
            </li>
          </ul>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;" v-loading="loading">
      <!-- Bottom Left: Top Turnover -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div style="font-weight: bold;">🔥 今日吸金指標股 (Top 5 成交值)</div>
          </template>
          <el-table :data="turnoverLeaders" style="width: 100%" size="small">
            <el-table-column prop="Stock_Name" label="名稱" width="100">
              <template #default="scope"><strong>{{ scope.row.Stock_Name }}</strong></template>
            </el-table-column>
            <el-table-column prop="Change_Pct" label="漲跌幅">
              <template #default="scope">
                <span :class="scope.row.Change_Pct > 0 ? 'up' : 'down'">
                  {{ scope.row.Change_Pct > 0 ? '+' : '' }}{{ scope.row.Change_Pct.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="Turnover_Value" label="成交金額(億)">
              <template #default="scope">{{ Math.round(scope.row.Turnover_Value) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- Bottom Right: Top Buy Industries -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div style="font-weight: bold;">🗺️ 法人湧入板塊 (Top 5 買超產業)</div>
          </template>
          <el-table :data="topIndustries" style="width: 100%" size="small">
            <el-table-column prop="Industry" label="產業別" />
            <el-table-column prop="Total_Net" label="買超張數">
              <template #default="scope">
                <span class="up">+{{ Math.round(scope.row.Total_Net) }}</span>
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
const breadth = ref(null)
const totals = ref(null)
const news = ref([])
const turnoverLeaders = ref([])
const topIndustries = ref([])

const fetchDashboardData = async () => {
  loading.value = true
  try {
    const [breadthRes, newsRes, turnoverRes, industryRes] = await Promise.all([
      axios.get('http://127.0.0.1:8000/api/market-breadth'),
      axios.get('http://127.0.0.1:8000/api/articles'),
      axios.get('http://127.0.0.1:8000/api/turnover-leaders'),
      axios.get('http://127.0.0.1:8000/api/industry-focus')
    ])
    
    breadth.value = breadthRes.data.breadth
    totals.value = breadthRes.data.totals
    news.value = newsRes.data
    turnoverLeaders.value = turnoverRes.data.slice(0, 5)
    topIndustries.value = industryRes.data.top_buy_industries.slice(0, 5)
    
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDashboardData()
})
</script>

<style scoped>
.dash-card {
  height: 180px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.card-title {
  font-size: 16px;
  font-weight: bold;
  color: #606266;
  margin-bottom: 15px;
}
.breadth-content {
  display: flex;
  justify-content: space-around;
  text-align: center;
  margin-bottom: 10px;
}
.stat-item span {
  display: block;
  font-size: 12px;
  color: #909399;
}
.stat-item strong {
  display: block;
  font-size: 24px;
  margin-top: 5px;
}
.up { color: #f56c6c; }
.down { color: #67c23a; }

.net-content {
  text-align: center;
}
.net-value {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 10px;
}
.sub-net {
  font-size: 13px;
}

.news-card .el-card__body {
  padding: 10px 20px;
}
.news-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.news-list li {
  margin-bottom: 10px;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.news-list a {
  color: #409EFF;
  text-decoration: none;
}
.news-list a:hover {
  text-decoration: underline;
}
</style>
