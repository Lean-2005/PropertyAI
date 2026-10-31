let map, markers=[], currentProject=null;
function initMap(){
  map=L.map('map').setView([19.1364,72.8240],13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap contributors'}).addTo(map);
}
function demo(q){document.getElementById('query').value=q;runSearch();}
async function runSearch(){
 const q=document.getElementById('query').value.trim(); if(!q)return;
 const role=document.getElementById('role').value;
 document.getElementById('resultTitle').innerText='AI is finding your projects…';
 const res=await fetch('/api/search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:q,user_type:role})});
 const data=await res.json(); render(data);
}
function render(data){
 document.getElementById('resultTitle').innerText=`${data.count} matching projects`;
 const f=data.filters;
 document.getElementById('resultSub').innerText=`${f.property_type||'All'} · ${f.bedrooms?f.bedrooms+' BHK · ':''}${f.location||'Mumbai'}${f.max_price_cr?' · ≤ ₹'+f.max_price_cr+' Cr':''}${f.completion_by?' · by '+f.completion_by:''}`;
 const box=document.getElementById('results'); box.innerHTML='';
 markers.forEach(x=>map.removeLayer(x));markers=[];
 if(!data.projects.length){box.innerHTML='<div class="empty"><div>⌕</div><h3>No exact matches</h3><p>Try widening the budget, location or completion date.</p></div>';return}
 data.projects.forEach((p,i)=>{
   const c=document.createElement('div');c.className='card';
   c.innerHTML=`<div class="card-top"><div><h3>${p.name}</h3><div class="meta">${p.location} · ${p.developer_name}</div></div><div class="price">₹${p.price_cr.toFixed(2)} Cr</div></div>
   <span class="badge">${p.property_type}</span><span class="badge">${p.bedrooms} BHK</span><span class="badge">Completion ${p.completion_date}</span>
   <div><span class="score">★ ${p.developer_score}/10 developer</span><button class="contact" onclick="openModal(${p.id},'${p.name.replace(/'/g,"\\'")}')">Contact developer</button></div>`;
   c.onclick=()=>map.setView([p.lat,p.lng],15);box.appendChild(c);
   const m=L.marker([p.lat,p.lng]).addTo(map).bindPopup(`<b>${p.name}</b><br>${p.bedrooms} BHK · ₹${p.price_cr} Cr<br>Developer score: ${p.developer_score}/10`);
   markers.push(m);
 });
 map.fitBounds(markers.map(m=>m.getLatLng()),{padding:[30,30]});
}
function openModal(id,name){currentProject=id;document.getElementById('modalProject').innerText=name;document.getElementById('modal').style.display='grid'}
function closeModal(){document.getElementById('modal').style.display='none'}
async function sendEnquiry(){
 const body={project_id:currentProject,name:document.getElementById('name').value,phone:document.getElementById('phone').value,email:document.getElementById('email').value,user_type:document.getElementById('role').value};
 const r=await fetch('/api/enquiry',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 const d=await r.json();document.getElementById('modalMsg').innerHTML='<p style="color:#7ee7c6">'+d.message+'</p>';
}
async function loadDashboard(){
 document.getElementById('dashboard').style.display='block';
 document.getElementById('dashboard').scrollIntoView({behavior:'smooth'});
 const role=document.getElementById('role').value;
 const d=await (await fetch('/api/dashboard/'+role)).json();
 document.getElementById('searches').innerHTML=d.searches.map(x=>`<div class="dash-item"><b>${x.query}</b><br>${new Date(x.created_at).toLocaleString()}</div>`).join('')||'<p class="meta">No searches yet.</p>';
 document.getElementById('enquiries').innerHTML=d.enquiries.map(x=>`<div class="dash-item"><b>${x.project_name}</b> · ${x.developer_name}<br>${x.name} · ${x.phone||x.email}</div>`).join('')||'<p class="meta">No enquiries yet.</p>';
}
document.getElementById('search').onclick=runSearch;
document.getElementById('query').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();runSearch()}});
document.getElementById('mic').onclick=()=>{
 const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;
 if(!SpeechRecognition){alert('Voice input is not supported in this browser. Try Chrome.');return}
 const r=new SpeechRecognition();r.lang='en-IN';r.interimResults=false;r.onresult=e=>{document.getElementById('query').value=e.results[0][0].transcript;runSearch()};r.start();
};
initMap();
