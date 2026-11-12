const API = "/api";
let token = localStorage.getItem("finpilot_token");
let user = null, categories = [], transactions = [], trendChart = null, categoryChart = null, authMode = "login", txKind = "expense";
const $ = id => document.getElementById(id);
const money = n => new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",maximumFractionDigits:2}).format(Number(n||0));
const today = () => new Date().toISOString().slice(0,10);
const monthNow = () => today().slice(0,7);
async function api(path, options={}) {
  const headers = {...(options.headers||{})};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (options.body && !(options.body instanceof FormData)) headers["Content-Type"]="application/json";
  const res = await fetch(API+path,{...options,headers});
  if (res.status===401 && token) { logout(); throw new Error("Session expired. Please sign in again."); }
  if (!res.ok) { let msg="Request failed"; try { const d=await res.json(); msg=d.detail||msg; } catch {} throw new Error(msg); }
  if (res.status===204) return null;
  const type=res.headers.get("content-type")||"";
  return type.includes("application/json")?res.json():res;
}
function toast(msg){$("toast").textContent=msg;$("toast").classList.add("show");setTimeout(()=>$("toast").classList.remove("show"),2600)}
function showApp(){ $("authView").classList.add("hidden");$("appView").classList.remove("hidden"); }
function showAuth(){ $("appView").classList.add("hidden");$("authView").classList.remove("hidden"); }
function logout(){token=null;user=null;localStorage.removeItem("finpilot_token");showAuth()}
function setAuthMode(mode){authMode=mode;document.querySelectorAll(".tab").forEach(b=>b.classList.toggle("active",b.dataset.mode===mode));$("nameWrap").classList.toggle("hidden",mode!=="register");$("authSubmit").textContent=mode==="login"?"Sign in":"Create account";$("password").autocomplete=mode==="login"?"current-password":"new-password";$("authError").textContent=""}
document.querySelectorAll(".tab").forEach(b=>b.addEventListener("click",()=>setAuthMode(b.dataset.mode)));
$("authForm").addEventListener("submit",async e=>{e.preventDefault();$("authError").textContent="";try{
 const payload={email:$("email").value.trim(),password:$("password").value};
 if(authMode==="register"){payload.name=$("name").value.trim();await api("/auth/register",{method:"POST",body:JSON.stringify(payload)});}
 const data=await api("/auth/login",{method:"POST",body:JSON.stringify({email:payload.email,password:payload.password})});
 token=data.access_token;localStorage.setItem("finpilot_token",token);await initApp();
 }catch(err){$("authError").textContent=err.message}});
async function initApp(){try{user=await api("/auth/me");$("userName").textContent=user.name;$("avatar").textContent=user.name[0].toUpperCase();showApp();$("monthPicker").value=monthNow();await loadCategories();await refresh();}catch(e){logout()}}
async function loadCategories(){categories=await api("/categories");const expense=categories.filter(c=>c.kind==="expense");$("budgetCategory").innerHTML='<option value="">All expenses</option>'+expense.map(c=>`<option value="${c.id}">${esc(c.name)}</option>`).join("");fillTxCategories();}
function fillTxCategories(){const list=categories.filter(c=>c.kind===txKind);$("txCategory").innerHTML='<option value="">Uncategorized</option>'+list.map(c=>`<option value="${c.id}">${esc(c.name)}</option>`).join("")}
async function refresh(){const month=$("monthPicker").value||monthNow();const [summary,trend,tx]=await Promise.all([api(`/analytics/summary?month=${month}`),api("/analytics/trend?months=6"),api(`/transactions?limit=100`)]);transactions=tx;renderSummary(summary);renderCharts(summary,trend);renderRows();await loadBudgets();await loadForecast();}
function renderSummary(s){$("balance").textContent=money(s.balance);$("income").textContent=money(s.income);$("expenses").textContent=money(s.expenses);$("txCount").textContent=s.transaction_count}
function renderCharts(s,trend){if(trendChart)trendChart.destroy();trendChart=new Chart($("trendChart"),{type:"bar",data:{labels:trend.map(x=>x.month),datasets:[{label:"Income",data:trend.map(x=>x.income),backgroundColor:"#4563e9",borderRadius:5},{label:"Expenses",data:trend.map(x=>x.expense),backgroundColor:"#f1a15b",borderRadius:5}]},options:{responsive:true,plugins:{legend:{position:"bottom",labels:{usePointStyle:true,boxWidth:7,font:{size:10}}}},scales:{x:{grid:{display:false}},y:{grid:{color:"#edf0f5"},ticks:{callback:v=>"₹"+v}}}}});
 if(categoryChart)categoryChart.destroy();const labels=s.categories.map(x=>x.name),vals=s.categories.map(x=>x.amount);categoryChart=new Chart($("categoryChart"),{type:"doughnut",data:{labels,datasets:[{data:vals,backgroundColor:["#4563e9","#f1a15b","#19a37a","#a78bfa","#e66b76","#42a5c7","#e3bd54"],borderWidth:0,hoverOffset:4}]},options:{cutout:"72%",plugins:{legend:{display:false}}}});
 $("categoryLegend").innerHTML=s.categories.slice(0,6).map((x,i)=>`<span><i class="dot" style="background:${["#4563e9","#f1a15b","#19a37a","#a78bfa","#e66b76","#42a5c7"][i]}"></i>${esc(x.name)} · ${money(x.amount)}</span>`).join("")||'<span class="muted">No expense data yet</span>'}
function categoryName(id){return categories.find(c=>c.id===id)?.name||"Uncategorized"}
function renderRows(){const month=$("monthPicker").value||monthNow();const recent=transactions.filter(t=>t.transaction_date.startsWith(month)).slice(0,5);$("recentRows").innerHTML=recent.map(row=>`<tr><td><strong>${esc(row.description)}</strong></td><td><span class="category-chip">${esc(categoryName(row.category_id))}</span></td><td>${row.transaction_date}</td><td class="amount-${row.kind}">${row.kind==="income"?"+":"−"}${money(row.amount)}</td></tr>`).join("")||'<tr><td colspan="4" class="muted">No transactions for this month yet.</td></tr>';
 const q=$("txSearch").value.toLowerCase(),kind=$("txKind").value;const list=transactions.filter(t=>(!q||t.description.toLowerCase().includes(q))&&(!kind||t.kind===kind));
 $("allRows").innerHTML=list.map(t=>`<tr><td><strong>${esc(t.description)}</strong></td><td>${t.kind}</td><td>${esc(categoryName(t.category_id))}</td><td>${t.transaction_date}</td><td class="amount-${t.kind}">${t.kind==="income"?"+":"−"}${money(t.amount)}</td><td><button class="action-btn" data-edit="${t.id}">Edit</button><button class="action-btn" data-delete="${t.id}">Delete</button></td></tr>`).join("")||'<tr><td colspan="6" class="muted">No matching transactions.</td></tr>'}
function esc(s){return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function openModal(item=null){$("txForm").reset();$("txId").value=item?.id||"";txKind=item?.kind||"expense";$("txType").value=txKind;document.querySelectorAll(".segmented button").forEach(b=>b.classList.toggle("selected",b.dataset.kind===txKind));fillTxCategories();$("txDescription").value=item?.description||"";$("txAmount").value=item?.amount||"";$("txDate").value=item?.transaction_date||today();$("txRecurring").checked=item?.recurring||false;$("txCategory").value=item?.category_id||"";$("modalTitle").textContent=item?"Edit transaction":"Add transaction";$("txError").textContent="";$("txModal").classList.remove("hidden")}
function closeModal(){$("txModal").classList.add("hidden")}
document.querySelectorAll(".segmented button").forEach(b=>b.addEventListener("click",()=>{txKind=b.dataset.kind;$("txType").value=txKind;document.querySelectorAll(".segmented button").forEach(x=>x.classList.toggle("selected",x===b));fillTxCategories()}));
["quickAdd","addTx"].forEach(id=>$(id).addEventListener("click",()=>openModal()));
["closeModal","cancelModal"].forEach(id=>$(id).addEventListener("click",closeModal));
$("txForm").addEventListener("submit",async e=>{e.preventDefault();const id=$("txId").value;const body={kind:txKind,description:$("txDescription").value.trim(),amount:Number($("txAmount").value),transaction_date:$("txDate").value,category_id:$("txCategory").value?Number($("txCategory").value):null,recurring:$("txRecurring").checked};try{await api(id?`/transactions/${id}`:"/transactions",{method:id?"PUT":"POST",body:JSON.stringify(body)});closeModal();await refresh();toast(id?"Transaction updated":"Transaction added")}catch(err){$("txError").textContent=err.message}});
$("allRows").addEventListener("click",async e=>{const edit=e.target.dataset.edit,del=e.target.dataset.delete;if(edit){const t=transactions.find(x=>x.id===Number(edit));if(t)openModal(t)}if(del&&confirm("Delete this transaction?")){try{await api(`/transactions/${del}`,{method:"DELETE"});await refresh();toast("Transaction deleted")}catch(err){toast(err.message)}}});
$("txSearch").addEventListener("input",renderRows);$("txKind").addEventListener("change",renderRows);
document.querySelectorAll(".nav-item").forEach(b=>b.addEventListener("click",()=>navigate(b.dataset.page)));
document.querySelectorAll("[data-goto]").forEach(b=>b.addEventListener("click",()=>navigate(b.dataset.goto)));
function navigate(page){document.querySelectorAll(".page").forEach(p=>p.classList.add("hidden"));$(page+"Page").classList.remove("hidden");document.querySelectorAll(".nav-item").forEach(b=>b.classList.toggle("active",b.dataset.page===page));$("pageTitle").textContent=({overview:"Good to see you",transactions:"Transactions",budgets:"Budget planning",reports:"Reports & insights"})[page]}
$("monthPicker").addEventListener("change",refresh);
async function loadBudgets(){try{const items=await api(`/budgets?month=${$("monthPicker").value||monthNow()}`);$("budgetList").innerHTML=items.map(b=>`<article class="budget-card"><div class="budget-meta"><span>${esc(b.name)}</span><button class="action-btn" data-budget-delete="${b.id}">Delete</button></div><h4>${money(b.spent)} <small class="muted">of ${money(b.monthly_limit)}</small></h4><div class="progress"><span class="${b.alert}" style="width:${Math.min(100,b.utilization)}%"></span></div><div class="budget-meta"><span>${b.utilization}% used</span><span>${money(b.remaining)} remaining</span></div>${b.alert!=="healthy"?`<p class="error">${b.alert==="exceeded"?"Budget exceeded":"You have used at least 80% of this budget."}</p>`:""}</article>`).join("")||'<p class="muted">No budgets created for this month.</p>'}catch(e){console.error(e)}}
$("budgetForm").addEventListener("submit",async e=>{e.preventDefault();try{await api("/budgets",{method:"POST",body:JSON.stringify({name:$("budgetName").value,category_id:$("budgetCategory").value?Number($("budgetCategory").value):null,monthly_limit:Number($("budgetLimit").value),month:$("monthPicker").value||monthNow()})});$("budgetForm").reset();await loadBudgets();toast("Budget created")}catch(err){toast(err.message)}});
$("budgetList").addEventListener("click",async e=>{const id=e.target.dataset.budgetDelete;if(id&&confirm("Delete this budget?")){await api(`/budgets/${id}`,{method:"DELETE"});await loadBudgets();toast("Budget deleted")}});
async function loadForecast(){try{const f=await api("/analytics/forecast");$("forecastValue").textContent=money(f.estimated_next_month_expense);$("forecastNote").textContent="Based on a three-month moving average."}catch(e){}}
$("downloadPdf").addEventListener("click",async()=>{try{const res=await fetch(`${API}/reports/monthly.pdf?month=${$("monthPicker").value||monthNow()}`,{headers:{Authorization:`Bearer ${token}`}});if(!res.ok)throw Error("Could not generate report");const blob=await res.blob(),url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download=`financial-report-${$("monthPicker").value}.pdf`;a.click();URL.revokeObjectURL(url)}catch(e){toast(e.message)}});
$("exportCsv").addEventListener("click",async()=>{const res=await fetch(API+"/transactions/export.csv",{headers:{Authorization:`Bearer ${token}`}});const blob=await res.blob(),url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download="transactions.csv";a.click();URL.revokeObjectURL(url)});
$("generateRecurring").addEventListener("click",async()=>{try{const r=await api("/recurring/generate",{method:"POST"});$("recurringResult").textContent=`Created ${r.created} transaction(s) for ${r.month}.`;await refresh()}catch(e){toast(e.message)}});
$("logout").addEventListener("click",logout);
if(token)initApp();else showAuth();
