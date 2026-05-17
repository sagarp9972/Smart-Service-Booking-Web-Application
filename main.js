document.addEventListener('DOMContentLoaded', function() {
  // Auto-dismiss alerts
  document.querySelectorAll('.alert.alert-dismissible').forEach(function(a){
    setTimeout(()=>bootstrap.Alert.getOrCreateInstance(a).close(), 4500);
  });

  // Min date on date inputs
  const today = new Date().toISOString().split('T')[0];
  document.querySelectorAll('input[type="date"]').forEach(i=>{ if(!i.min) i.min=today; });

  // Notification count
  function updateNotif(){
    fetch('/notifications/count/').then(r=>r.json()).then(d=>{
      const b=document.getElementById('notif-count');
      if(b){ if(d.count>0){b.textContent=d.count;b.style.display='inline';}else{b.style.display='none';} }
    }).catch(()=>{});
  }
  updateNotif(); setInterval(updateNotif,30000);

  // Time slot loader
  const dateInp   = document.getElementById('booking-date') || document.querySelector('input[name="date"]');
  const slotsBox  = document.getElementById('slots-container');
  const slotHid   = document.getElementById('slot-id-hidden');
  const timeHid   = document.getElementById('id_time');
  const svcMeta   = document.getElementById('service-id-meta');

  if(dateInp && slotsBox && svcMeta){
    dateInp.addEventListener('change', function(){
      const date=this.value, sid=svcMeta.dataset.id;
      slotsBox.innerHTML='<p class="text-muted small"><i class="fas fa-spinner fa-spin me-1"></i>Loading slots...</p>';
      fetch('/services/'+sid+'/slots/?date='+date).then(r=>r.json()).then(data=>{
        if(!data.slots.length){ slotsBox.innerHTML='<p class="text-muted small">No slots for this date.</p>'; return; }
        slotsBox.innerHTML='<div class="d-flex flex-wrap gap-2">'+
          data.slots.map(s=>`<button type="button" class="time-slot-btn${s.available?'':' booked'}"
            data-slot-id="${s.id}" data-time="${s.time}" ${s.available?'':'disabled'}>
            <i class="far fa-clock me-1"></i>${s.time}${s.available?'':' <span class="badge bg-danger ms-1" style="font-size:.6rem">Full</span>'}
          </button>`).join('')+'</div>';
        slotsBox.querySelectorAll('.time-slot-btn:not(.booked)').forEach(btn=>{
          btn.addEventListener('click',function(){
            slotsBox.querySelectorAll('.time-slot-btn').forEach(b=>b.classList.remove('selected'));
            this.classList.add('selected');
            if(slotHid) slotHid.value=this.dataset.slotId;
            if(timeHid) timeHid.value=this.dataset.time;
          });
        });
      }).catch(()=>{ slotsBox.innerHTML='<p class="text-danger small">Failed to load slots.</p>'; });
    });
  }

  // Star rating UI
  const ratingInp = document.getElementById('id_rating');
  const starUI    = document.getElementById('star-rating-ui');
  if(starUI && ratingInp){
    for(let i=1;i<=5;i++){
      const s=document.createElement('i');
      s.className='fas fa-star fa-lg me-1'; s.style.cursor='pointer'; s.style.color='#D1D5DB'; s.dataset.v=i;
      s.addEventListener('click',function(){ ratingInp.value=this.dataset.v; paint(this.dataset.v); });
      s.addEventListener('mouseover',function(){ paint(this.dataset.v); });
      starUI.appendChild(s);
    }
    starUI.addEventListener('mouseleave',()=>paint(ratingInp.value||0));
    function paint(v){ starUI.querySelectorAll('i').forEach((s,i)=>s.style.color=i<v?'#F59E0B':'#D1D5DB'); }
  }

  // Booking form validation
  const bkForm=document.querySelector('form.booking-form');
  if(bkForm) bkForm.addEventListener('submit',function(e){
    const d=this.querySelector('input[name="date"]');
    if(d&&d.value&&new Date(d.value)<new Date(today)){
      e.preventDefault(); alert('Please select a future date.'); d.focus();
    }
  });

  // Profile pic preview
  const picInp=document.getElementById('id_profile_pic');
  const picPrv=document.getElementById('profile-pic-preview');
  if(picInp&&picPrv) picInp.addEventListener('change',function(){
    const f=this.files[0]; if(f){const r=new FileReader(); r.onload=e=>picPrv.src=e.target.result; r.readAsDataURL(f);}
  });
});
