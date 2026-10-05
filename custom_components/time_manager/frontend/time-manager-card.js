const TIME_MANAGER_VERSION = "0.2.0";

const TM_I18N = {
  de: {
    title:"Zeitmanager", on:"EIN", off:"AUS", disabled:"DEAKTIVIERT",
    next:"Nächste Aktion", timer:"Timer", schedules:"Zeitpläne", noDevices:"Noch keine Geräte.",
    addFirst:"Mit + das erste Gerät anlegen.", add:"Gerät hinzufügen", edit:"Gerät bearbeiten",
    remove:"Gerät entfernen", name:"Name", entity:"Entität", enabled:"Zeitsteuerung aktiv",
    climateMode:"Klima-Modus", targetTemp:"Solltemperatur", coverOn:"Position EIN / Öffnen",
    coverOff:"Position AUS / Schließen", save:"Speichern", cancel:"Abbrechen", close:"Schließen",
    addSchedule:"Zeitplan hinzufügen", editSchedule:"Zeitplan bearbeiten", removeSchedule:"Zeitplan löschen",
    scheduleName:"Name des Zeitplans", weekdays:"Wochentage", start:"Einschalten / Öffnen",
    end:"Ausschalten / Schließen", fixedTime:"Uhrzeit", sunrise:"Sonnenaufgang", sunset:"Sonnenuntergang",
    time:"Uhrzeit", offset:"Versatz (Minuten)", active:"Aktiv", everyDay:"Täglich",
    mo:"Mo",tu:"Di",we:"Mi",th:"Do",fr:"Fr",sa:"Sa",su:"So",
    timerStart:"Timer starten", minutes:"Minuten", timerCancel:"Timer abbrechen",
    turnOffToo:"Gerät dabei ausschalten", managerOn:"Gesamte Zeitsteuerung",
    selectDevice:"Bitte zuerst ein Gerät auswählen.", confirmRemove:"wirklich entfernen?",
    noSchedules:"Noch keine Zeitpläne.", timerRemaining:"Timer läuft noch", error:"Fehler",
    status:"Status", version:"Version", customTimer:"Eigener Timer", minutesShort:"min",
    timerPresets:"Timer-Schnellwahl", timerPresetsHint:"Die drei Zeiten können für jedes Gerät getrennt festgelegt werden.",
    nextSwitch:"Nächste Schaltung",
    entityHint:"Unterstützt: switch, light, climate, cover, fan",
    climateHint:"Bei deiner HANTECH kann z. B. heat_cool statt heat verwendet werden.",
    coverHint:"0 = geschlossen, 100 = vollständig geöffnet."
  },
  en: {
    title:"Time Manager", on:"ON", off:"OFF", disabled:"DISABLED",
    next:"Next action", timer:"Timer", schedules:"Schedules", noDevices:"No devices yet.",
    addFirst:"Use + to add the first device.", add:"Add device", edit:"Edit device",
    remove:"Remove device", name:"Name", entity:"Entity", enabled:"Time control enabled",
    climateMode:"Climate mode", targetTemp:"Target temperature", coverOn:"ON / open position",
    coverOff:"OFF / closed position", save:"Save", cancel:"Cancel", close:"Close",
    addSchedule:"Add schedule", editSchedule:"Edit schedule", removeSchedule:"Delete schedule",
    scheduleName:"Schedule name", weekdays:"Weekdays", start:"Turn on / open",
    end:"Turn off / close", fixedTime:"Time", sunrise:"Sunrise", sunset:"Sunset",
    time:"Time", offset:"Offset (minutes)", active:"Active", everyDay:"Daily",
    mo:"Mon",tu:"Tue",we:"Wed",th:"Thu",fr:"Fri",sa:"Sat",su:"Sun",
    timerStart:"Start timer", minutes:"Minutes", timerCancel:"Cancel timer",
    turnOffToo:"Also turn device off", managerOn:"Master time control",
    selectDevice:"Please select a device first.", confirmRemove:"really remove?",
    noSchedules:"No schedules yet.", timerRemaining:"Timer remaining", error:"Error",
    status:"Status", version:"Version", customTimer:"Custom timer", minutesShort:"min",
    timerPresets:"Timer presets", timerPresetsHint:"The three times can be configured separately for each device.",
    nextSwitch:"Next switch",
    entityHint:"Supported: switch, light, climate, cover, fan",
    climateHint:"Some climate devices require heat_cool instead of heat.",
    coverHint:"0 = closed, 100 = fully open."
  }
};

class TimeManagerCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode:"open"});
    this._config = {};
    this._hass = null;
    this._selectedId = null;
    this._modal = null;
    this._renderQueued = false;
  }

  setConfig(config) {
    if (!config.entity) throw new Error("Bitte 'entity:' mit dem Zeitmanager-Sensor angeben.");
    this._config = config;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._modal) this._queueRender();
  }

  getCardSize() {
    const n = this._state()?.attributes?.devices?.length || 1;
    return Math.max(5, Math.ceil((180 + n * 68) / 50));
  }

  _queueRender() {
    if (this._renderQueued) return;
    this._renderQueued = true;
    requestAnimationFrame(() => { this._renderQueued = false; this._render(); });
  }

  _state() { return this._hass?.states?.[this._config.entity]; }
  _attrs() { return this._state()?.attributes || {}; }
  _devices() { return this._attrs().devices || []; }
  _entryId() { return this._attrs().entry_id; }

  _lang() {
    const configured = String(this._attrs().language || "auto").toLowerCase();
    if (configured !== "auto" && TM_I18N[configured]) return configured;
    const lang = String(this._hass?.locale?.language || this._hass?.language || "de").toLowerCase().split("-")[0];
    return TM_I18N[lang] ? lang : "en";
  }
  _t(k) { return TM_I18N[this._lang()]?.[k] || k; }
  _esc(v) {
    return String(v ?? "").replaceAll("&","&amp;").replaceAll("<","&lt;")
      .replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");
  }

  _selected() {
    return this._devices().find(d => d.id === this._selectedId) || null;
  }

  _domain(entity) { return String(entity || "").split(".")[0]; }

  _fmtWhen(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    const opts = {weekday:"short", hour:"2-digit", minute:"2-digit"};
    return new Intl.DateTimeFormat(this._lang() === "de" ? "de-DE" : "en-GB", opts).format(d);
  }

  _fmtRemaining(sec) {
    sec = Math.max(0, Number(sec || 0));
    const h = Math.floor(sec/3600);
    const m = Math.floor((sec%3600)/60);
    const s = Math.floor(sec%60);
    return h > 0 ? `${h}:${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}` : `${m}:${String(s).padStart(2,"0")}`;
  }

  async _call(service, data={}) {
    if (!this._hass || !this._entryId()) return;
    try {
      await this._hass.callService("time_manager", service, {config_entry_id:this._entryId(), ...data});
    } catch (err) {
      alert(`${this._t("error")}: ${err?.message || err}`);
    }
  }

  _entityOptions() {
    if (!this._hass) return "";
    return Object.keys(this._hass.states)
      .filter(id => ["switch","light","climate","cover","fan"].includes(this._domain(id)))
      .sort()
      .map(id => `<option value="${this._esc(id)}"></option>`).join("");
  }

  _styles() {
    return `
      :host{display:block}
      ha-card{padding:16px;overflow:hidden}
      .head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px}
      .title{font-size:20px;font-weight:600}
      .master{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--secondary-text-color)}
      .layout{display:grid;grid-template-columns:minmax(0,1fr) 48px;gap:10px}
      .list{display:flex;flex-direction:column;gap:8px;min-width:0}
      .empty{padding:28px 14px;text-align:center;border:1px dashed var(--divider-color);border-radius:12px;color:var(--secondary-text-color)}
      .row{display:grid;grid-template-columns:30px minmax(0,1fr);align-items:center;gap:10px;padding:10px 12px;border:1px solid var(--divider-color);border-radius:12px;cursor:pointer;background:var(--ha-card-background,var(--card-background-color))}
      .row.sel{outline:2px solid var(--primary-color);outline-offset:-2px}
      .row.disabled{opacity:.62}
      .deviceToggle{display:flex;align-items:center;justify-content:center;cursor:pointer}
      .deviceToggle input{width:18px;height:18px;cursor:pointer}
      .name{font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
      .sub{font-size:12px;color:var(--secondary-text-color);margin-top:3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
      .nextLine{font-size:12px;color:var(--secondary-text-color);margin-top:5px}
      .timer{color:var(--primary-color);font-weight:600}
      .tools{display:flex;flex-direction:column;gap:8px;justify-content:center;align-self:stretch}
      button.icon{width:44px;height:44px;border-radius:12px;border:1px solid var(--divider-color);background:var(--card-background-color);color:var(--primary-text-color);font-size:22px;cursor:pointer}
      button.icon:hover{background:var(--secondary-background-color)}
      .timerActions{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap}
      .timerActions button,.smallbtn,.primary{border:1px solid var(--divider-color);border-radius:9px;padding:6px 10px;background:var(--secondary-background-color);color:var(--primary-text-color);cursor:pointer}
      .primary{background:var(--primary-color);color:var(--text-primary-color,#fff);border-color:var(--primary-color)}
      .foot{margin-top:12px;font-size:11px;color:var(--secondary-text-color);text-align:right}
      .overlay{position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,.48);display:flex;align-items:center;justify-content:center;padding:18px}
      .dialog{width:min(680px,100%);max-height:88vh;overflow:auto;background:var(--card-background-color);color:var(--primary-text-color);border-radius:16px;box-shadow:0 12px 40px rgba(0,0,0,.35);padding:18px}
      .dialog h2{font-size:20px;margin:0 0 14px}
      .field{margin:10px 0}
      .field label{display:block;font-size:12px;color:var(--secondary-text-color);margin-bottom:5px}
      input,select{box-sizing:border-box;width:100%;padding:9px 10px;border-radius:9px;border:1px solid var(--divider-color);background:var(--secondary-background-color);color:var(--primary-text-color)}
      input[type=checkbox]{width:auto}
      .check{display:flex;align-items:center;gap:8px}
      .grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
      .grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
      .actions{display:flex;justify-content:flex-end;gap:8px;margin-top:16px}
      .hint{font-size:11px;color:var(--secondary-text-color);margin-top:4px}
      .schedule{border:1px solid var(--divider-color);border-radius:10px;padding:9px;margin-top:8px;display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center}
      .schTitle{font-weight:600}
      .schSub{font-size:11px;color:var(--secondary-text-color);margin-top:2px}
      .weekdays{display:flex;gap:5px;flex-wrap:wrap}
      .day{display:flex;align-items:center;gap:3px;padding:5px 7px;border-radius:8px;background:var(--secondary-background-color);font-size:12px}
      .section{margin-top:15px;padding-top:12px;border-top:1px solid var(--divider-color)}
      @media(max-width:560px){.grid2,.grid3{grid-template-columns:1fr}.row{grid-template-columns:28px minmax(0,1fr)}}
    `;
  }

  _render() {
    if (!this.shadowRoot) return;
    const st = this._state();
    if (!st) {
      this.shadowRoot.innerHTML = `<style>${this._styles()}</style><ha-card><div class="empty">Zeitmanager-Sensor nicht gefunden: ${this._esc(this._config.entity)}</div></ha-card>`;
      return;
    }

    const devices = this._devices();
    if (this._selectedId && !devices.some(d => d.id === this._selectedId)) this._selectedId = null;

    const rows = devices.map(d => {
      const next = d.next_action;
      const nextText = d.enabled && next ? `${next.action === "on" ? this._t("on") : this._t("off")} · ${this._fmtWhen(next.at)}` : "—";
      return `
        <div class="row ${d.id===this._selectedId?"sel":""} ${!d.enabled?"disabled":""}" data-id="${d.id}">
          <label class="deviceToggle" title="${this._t("enabled")}">
            <input type="checkbox" data-device-enabled="${d.id}" ${d.enabled?"checked":""}>
          </label>
          <div>
            <div class="name">${this._esc(d.name)}</div>
            <div class="sub">${this._esc(d.entity_id)}</div>
            <div class="nextLine">${this._t("nextSwitch")}: ${nextText}</div>
          </div>
        </div>`;
    }).join("");

    this.shadowRoot.innerHTML = `
      <style>${this._styles()}</style>
      <ha-card>
        <div class="head">
          <div class="title">${this._esc(this._config.title || this._t("title"))}</div>
          <label class="master"><input id="master" type="checkbox" ${this._attrs().enabled?"checked":""}> ${this._t("managerOn")}</label>
        </div>
        <div class="layout">
          <div class="list">${rows || `<div class="empty"><b>${this._t("noDevices")}</b><br>${this._t("addFirst")}</div>`}</div>
          <div class="tools">
            <button class="icon" id="add" title="${this._t("add")}">+</button>
            <button class="icon" id="remove" title="${this._t("remove")}">−</button>
            <button class="icon" id="edit" title="${this._t("edit")}">✎</button>
          </div>
        </div>
        <div class="foot">${this._t("version")} ${this._esc(this._attrs().version || TIME_MANAGER_VERSION)}</div>
        <div id="modalHost"></div>
      </ha-card>`;

    this.shadowRoot.querySelectorAll(".row").forEach(el => el.addEventListener("click", e => {
      if (e.target.closest("button,input,label")) return;
      this._selectedId = el.dataset.id;
      this._render();
    }));
    this.shadowRoot.querySelectorAll("[data-device-enabled]").forEach(cb => cb.addEventListener("change", async e => {
      e.stopPropagation();
      await this._call("set_device_enabled",{device_id:cb.dataset.deviceEnabled,enabled:cb.checked});
    }));
    this.shadowRoot.querySelector("#add")?.addEventListener("click", () => this._openDevice(null));
    this.shadowRoot.querySelector("#edit")?.addEventListener("click", () => {
      const d=this._selected(); if (!d) return alert(this._t("selectDevice")); this._openDevice(d);
    });
    this.shadowRoot.querySelector("#remove")?.addEventListener("click", async () => {
      const d=this._selected(); if (!d) return alert(this._t("selectDevice"));
      if (confirm(`${d.name} ${this._t("confirmRemove")}`)) {
        await this._call("remove_device",{device_id:d.id}); this._selectedId=null;
      }
    });
    this.shadowRoot.querySelector("#master")?.addEventListener("change", e => this._call("set_enabled",{enabled:e.target.checked}));

  }

  _openDevice(device) {
    this._modal = {type:"device", id:device?.id || null};
    const d = device || {
      name:"",entity_id:"",enabled:true,climate_mode:"heat_cool",target_temp:20,
      cover_on_position:100,cover_off_position:0,timer_presets:[30,60,90],schedules:[]
    };
    const host=this.shadowRoot.querySelector("#modalHost");
    host.innerHTML = `
      <div class="overlay" id="overlay"><div class="dialog" id="deviceDialog">
        <h2>${device?this._t("edit"):this._t("add")}</h2>
        <div class="grid2">
          <div class="field"><label>${this._t("name")}</label><input id="dName" value="${this._esc(d.name)}"></div>
          <div class="field"><label>${this._t("entity")}</label><input id="dEntity" list="tmEntities" value="${this._esc(d.entity_id)}"><datalist id="tmEntities">${this._entityOptions()}</datalist><div class="hint">${this._t("entityHint")}</div></div>
        </div>
        <div class="field check"><input id="dEnabled" type="checkbox" ${d.enabled?"checked":""}><label for="dEnabled">${this._t("enabled")}</label></div>
        <div id="domainFields"></div>
        <div class="section">
          <b>${this._t("timerPresets")}</b>
          <div class="grid3">
            <div class="field"><label>1 (${this._t("minutesShort")})</label><input id="dTimer1" type="number" min="1" max="10080" value="${this._esc((d.timer_presets||[30,60,90])[0] ?? 30)}"></div>
            <div class="field"><label>2 (${this._t("minutesShort")})</label><input id="dTimer2" type="number" min="1" max="10080" value="${this._esc((d.timer_presets||[30,60,90])[1] ?? 60)}"></div>
            <div class="field"><label>3 (${this._t("minutesShort")})</label><input id="dTimer3" type="number" min="1" max="10080" value="${this._esc((d.timer_presets||[30,60,90])[2] ?? 90)}"></div>
          </div>
          <div class="hint">${this._t("timerPresetsHint")}</div>
          ${device ? `<div class="timerActions">
            <button data-device-timer="1">${this._esc((d.timer_presets||[30,60,90])[0] ?? 30)} min</button>
            <button data-device-timer="2">${this._esc((d.timer_presets||[30,60,90])[1] ?? 60)} min</button>
            <button data-device-timer="3">${this._esc((d.timer_presets||[30,60,90])[2] ?? 90)} min</button>
            <button id="customTimer">…</button>
            ${d.timer_remaining_s>0?`<button id="cancelTimer">× ${this._t("timer")}</button>`:""}
          </div>` : ""}
        </div>
        ${device ? `
        <div class="section">
          <div style="display:flex;align-items:center;justify-content:space-between"><b>${this._t("schedules")}</b><button class="smallbtn" id="addSchedule">+ ${this._t("addSchedule")}</button></div>
          <div id="scheduleList"></div>
        </div>` : ""}
        <div class="actions"><button class="smallbtn" id="cancel">${this._t("cancel")}</button><button class="primary" id="saveDevice">${this._t("save")}</button></div>
      </div></div>`;

    const renderDomain = () => {
      const entity=host.querySelector("#dEntity").value;
      const domain=this._domain(entity);
      const box=host.querySelector("#domainFields");
      if (domain==="climate") box.innerHTML=`
        <div class="grid2">
          <div class="field"><label>${this._t("climateMode")}</label>
            <select id="dClimate"><option value="heat_cool">heat_cool</option><option value="heat">heat</option><option value="cool">cool</option><option value="dry">dry</option><option value="fan_only">fan_only</option></select>
            <div class="hint">${this._t("climateHint")}</div>
          </div>
          <div class="field"><label>${this._t("targetTemp")}</label><input id="dTemp" type="number" step="0.5" value="${this._esc(d.target_temp ?? 20)}"></div>
        </div>`;
      else if (domain==="cover") box.innerHTML=`
        <div class="grid2">
          <div class="field"><label>${this._t("coverOn")}</label><input id="dCoverOn" type="number" min="0" max="100" value="${this._esc(d.cover_on_position ?? 100)}"></div>
          <div class="field"><label>${this._t("coverOff")}</label><input id="dCoverOff" type="number" min="0" max="100" value="${this._esc(d.cover_off_position ?? 0)}"></div>
        </div><div class="hint">${this._t("coverHint")}</div>`;
      else box.innerHTML="";
      if (domain==="climate") {
        const s=box.querySelector("#dClimate"); if(s) s.value=d.climate_mode || "heat_cool";
      }
    };
    renderDomain();
    host.querySelector("#dEntity").addEventListener("change",renderDomain);
    host.querySelector("#dEntity").addEventListener("input",renderDomain);

    const close=()=>{this._modal=null;host.innerHTML="";this._queueRender();};
    host.querySelector("#cancel").addEventListener("click",close);
    host.querySelector("#overlay").addEventListener("click",e=>{if(e.target.id==="overlay")close();});

    if (device) {
      this._renderSchedules(device);
      host.querySelector("#addSchedule").addEventListener("click",()=>this._openSchedule(device,null));
      host.querySelectorAll("[data-device-timer]").forEach(b=>b.addEventListener("click",async()=>{
        const input=host.querySelector(`#dTimer${b.dataset.deviceTimer}`);
        const minutes=Math.max(1,Number(input?.value||0));
        if(minutes>0) await this._call("start_timer",{device_id:device.id,duration_min:minutes});
      }));
      host.querySelector("#customTimer")?.addEventListener("click",async()=>{
        const v=prompt(`${this._t("minutes")}:`,"45");
        if(v && Number(v)>0) await this._call("start_timer",{device_id:device.id,duration_min:Number(v)});
      });
      host.querySelector("#cancelTimer")?.addEventListener("click",async()=>{
        await this._call("cancel_timer",{device_id:device.id,turn_off:true});
      });
    }

    host.querySelector("#saveDevice").addEventListener("click",async()=>{
      const entity=host.querySelector("#dEntity").value.trim();
      const domain=this._domain(entity);
      const data={
        name:host.querySelector("#dName").value.trim() || entity,
        entity_id:entity,
        enabled:host.querySelector("#dEnabled").checked,
        timer_presets:[1,2,3].map(i=>Math.max(1,Math.min(10080,Number(host.querySelector(`#dTimer${i}`).value||[30,60,90][i-1])))),
      };
      if(domain==="climate"){
        data.climate_mode=host.querySelector("#dClimate").value;
        const t=host.querySelector("#dTemp").value; data.target_temp=t===""?null:Number(t);
      }
      if(domain==="cover"){
        data.cover_on_position=Number(host.querySelector("#dCoverOn").value);
        data.cover_off_position=Number(host.querySelector("#dCoverOff").value);
      }
      if(!data.entity_id || !["switch","light","climate","cover","fan"].includes(domain)) return alert(this._t("entityHint"));
      if(device) await this._call("update_device",{device_id:device.id,...data});
      else await this._call("add_device",data);
      close();
    });
  }

  _renderSchedules(device) {
    const list=this.shadowRoot.querySelector("#scheduleList");
    if(!list) return;
    const names=[this._t("mo"),this._t("tu"),this._t("we"),this._t("th"),this._t("fr"),this._t("sa"),this._t("su")];
    const describeEvent=(s,prefix)=>{
      const type=s[prefix+"_type"];
      let txt=type==="time" ? s[prefix+"_time"] : this._t(type);
      const off=Number(s[prefix+"_offset_min"]||0);
      if(off) txt += ` ${off>0?"+":""}${off} min`;
      return txt;
    };
    list.innerHTML=(device.schedules||[]).map(s=>`
      <div class="schedule">
        <div>
          <div class="schTitle">${this._esc(s.name)} ${!s.enabled?`· ${this._t("disabled")}`:""}</div>
          <div class="schSub">${s.weekdays.map(i=>names[i]).join(" ")} · ${describeEvent(s,"start")} → ${describeEvent(s,"end")}</div>
        </div>
        <div><button class="smallbtn" data-edit-sch="${s.id}">✎</button> <button class="smallbtn" data-del-sch="${s.id}">−</button></div>
      </div>`).join("") || `<div class="hint" style="padding:10px 0">${this._t("noSchedules")}</div>`;

    list.querySelectorAll("[data-edit-sch]").forEach(b=>b.addEventListener("click",()=>this._openSchedule(device,(device.schedules||[]).find(s=>s.id===b.dataset.editSch))));
    list.querySelectorAll("[data-del-sch]").forEach(b=>b.addEventListener("click",async()=>{
      const s=(device.schedules||[]).find(x=>x.id===b.dataset.delSch);
      if(s && confirm(`${s.name} ${this._t("confirmRemove")}`)){
        await this._call("remove_schedule",{device_id:device.id,schedule_id:s.id});
        this._modal=null; this._queueRender();
      }
    }));
  }

  _openSchedule(device,schedule) {
    const host=this.shadowRoot.querySelector("#modalHost");
    const s=schedule || {
      name:"Zeitplan",enabled:true,weekdays:[0,1,2,3,4,5,6],
      start_type:"time",start_time:"08:00",start_offset_min:0,
      end_type:"time",end_time:"10:00",end_offset_min:0
    };
    this._modal={type:"schedule",device:device.id,id:schedule?.id||null};
    const dayKeys=["mo","tu","we","th","fr","sa","su"];
    host.innerHTML=`
      <div class="overlay" id="overlay"><div class="dialog">
        <h2>${schedule?this._t("editSchedule"):this._t("addSchedule")}</h2>
        <div class="grid2">
          <div class="field"><label>${this._t("scheduleName")}</label><input id="sName" value="${this._esc(s.name)}"></div>
          <div class="field check"><input id="sEnabled" type="checkbox" ${s.enabled?"checked":""}><label for="sEnabled">${this._t("active")}</label></div>
        </div>
        <div class="field"><label>${this._t("weekdays")}</label><div class="weekdays">
          ${dayKeys.map((k,i)=>`<label class="day"><input type="checkbox" data-day="${i}" ${s.weekdays.includes(i)?"checked":""}> ${this._t(k)}</label>`).join("")}
        </div></div>
        ${this._eventFields("start",s)}
        ${this._eventFields("end",s)}
        <div class="actions"><button class="smallbtn" id="cancel">${this._t("cancel")}</button><button class="primary" id="saveSchedule">${this._t("save")}</button></div>
      </div></div>`;

    const updateVisibility=(prefix)=>{
      const type=host.querySelector(`#${prefix}Type`).value;
      host.querySelector(`#${prefix}TimeWrap`).style.display=type==="time"?"block":"none";
    };
    ["start","end"].forEach(p=>{
      host.querySelector(`#${p}Type`).addEventListener("change",()=>updateVisibility(p)); updateVisibility(p);
    });
    const back=()=>this._openDevice(this._devices().find(d=>d.id===device.id) || device);
    host.querySelector("#cancel").addEventListener("click",back);
    host.querySelector("#overlay").addEventListener("click",e=>{if(e.target.id==="overlay")back();});
    host.querySelector("#saveSchedule").addEventListener("click",async()=>{
      const weekdays=[...host.querySelectorAll("[data-day]:checked")].map(x=>Number(x.dataset.day));
      if(!weekdays.length) return alert(this._t("weekdays"));
      const data={
        name:host.querySelector("#sName").value.trim() || "Zeitplan",
        enabled:host.querySelector("#sEnabled").checked,
        weekdays,
        start_type:host.querySelector("#startType").value,
        start_time:host.querySelector("#startTime").value || "00:00",
        start_offset_min:Number(host.querySelector("#startOffset").value || 0),
        end_type:host.querySelector("#endType").value,
        end_time:host.querySelector("#endTime").value || "00:00",
        end_offset_min:Number(host.querySelector("#endOffset").value || 0),
      };
      if(schedule) await this._call("update_schedule",{device_id:device.id,schedule_id:schedule.id,...data});
      else await this._call("add_schedule",{device_id:device.id,...data});
      this._modal=null; this._queueRender();
    });
  }

  _eventFields(prefix,s) {
    const isStart=prefix==="start";
    return `
      <div class="section"><b>${isStart?this._t("start"):this._t("end")}</b>
        <div class="grid2">
          <div class="field"><label>Typ</label><select id="${prefix}Type">
            <option value="time" ${s[prefix+"_type"]==="time"?"selected":""}>${this._t("fixedTime")}</option>
            <option value="sunrise" ${s[prefix+"_type"]==="sunrise"?"selected":""}>${this._t("sunrise")}</option>
            <option value="sunset" ${s[prefix+"_type"]==="sunset"?"selected":""}>${this._t("sunset")}</option>
          </select></div>
          <div class="field" id="${prefix}TimeWrap"><label>${this._t("time")}</label><input id="${prefix}Time" type="time" value="${this._esc(s[prefix+"_time"])}"></div>
        </div>
        <div class="field"><label>${this._t("offset")}</label><input id="${prefix}Offset" type="number" value="${this._esc(s[prefix+"_offset_min"]||0)}"></div>
      </div>`;
  }
}

customElements.define("time-manager-card", TimeManagerCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type:"time-manager-card",
  name:"Zeitmanager",
  description:"Zeit-, Sonnen- und Timersteuerung für Home Assistant"
});
console.info(`%c ZEITMANAGER %c v${TIME_MANAGER_VERSION} `, "background:#03a9f4;color:white;font-weight:bold", "background:#eee;color:#333");
