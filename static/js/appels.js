/* ============================================================
   SmartLife AI — Appels audio / vidéo (WebRTC)
   Chargé depuis base.html, disponible sur toutes les pages.
   ============================================================ */

const ICE_SERVERS = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
    // Serveur TURN gratuit (Open Relay Project) — sans lui, un appel échoue à
    // se connecter dès que l'une des deux personnes est derrière un réseau
    // plus restrictif (courant sur certains réseaux mobiles/campus). Limite
    // de débit sur l'offre gratuite ; largement suffisant pour un usage
    // étudiant. Pour une utilisation à plus grande échelle, remplacer par
    // des identifiants TURN dédiés (ex. metered.ca, Twilio).
    { urls: 'turn:openrelay.metered.ca:80', username: 'openrelayproject', credential: 'openrelayproject' },
    { urls: 'turn:openrelay.metered.ca:443', username: 'openrelayproject', credential: 'openrelayproject' },
    { urls: 'turn:openrelay.metered.ca:443?transport=tcp', username: 'openrelayproject', credential: 'openrelayproject' },
  ],
};

const Appels = {
  socket: null,
  monUserId: null,
  monNom: null,
  callId: null,
  mode: null,          // 'prive' | 'groupe'
  typeAppel: null,      // 'audio' | 'video'
  autrePartieId: null,  // pour un appel privé
  autrePartieNom: null,
  groupeId: null,
  fluxLocal: null,
  connexions: {},       // { user_id: RTCPeerConnection }
  elementsVideoDistants: {}, // { user_id: HTMLVideoElement }
  sonnerie: null,
  enAppel: false,

  init(socket, userId, nom) {
    this.socket = socket;
    this.monUserId = userId;
    this.monNom = nom;
    this.sonnerie = document.getElementById('audio-sonnerie');

    socket.on('appel_entrant', (data) => this._surAppelEntrant(data));
    socket.on('appel_initie', (data) => { this.callId = data.call_id; });
    socket.on('appel_refuse', () => this._terminerLocalement("L'appel n'a pas été accepté."));
    socket.on('appel_participants', (data) => this._surParticipants(data));
    socket.on('appel_nouveau_participant', (data) => this._surNouveauParticipant(data));
    socket.on('appel_participant_parti', (data) => this._surParticipantParti(data));
    socket.on('appel_offre', (data) => this._surOffre(data));
    socket.on('appel_reponse', (data) => this._surReponse(data));
    socket.on('appel_ice', (data) => this._surIce(data));
  },

  // ── Démarrer un appel ────────────────────────────────────────
  async demarrerAppelPrive(destinataireId, destinataireNom, type) {
    if (this.enAppel) { alert('Tu es déjà en appel.'); return; }
    this.mode = 'prive';
    this.typeAppel = type;
    this.autrePartieId = destinataireId;
    this.autrePartieNom = destinataireNom;

    const ok = await this._demarrerMedia(type);
    if (!ok) return;

    this._afficherEcranAppel('appel-sortant', destinataireNom);
    this.socket.emit('appel_initier', { destinataire_id: destinataireId, type });
    // callId arrive via 'appel_initie' ; on rejoint dès qu'on l'a
    const attendreCallId = setInterval(() => {
      if (this.callId) {
        clearInterval(attendreCallId);
        this.enAppel = true;
        this.socket.emit('appel_rejoindre', { call_id: this.callId });
      }
    }, 100);
  },

  async demarrerAppelGroupe(groupeId, groupeNom, type) {
    if (this.enAppel) { alert('Tu es déjà en appel.'); return; }
    this.mode = 'groupe';
    this.typeAppel = type;
    this.groupeId = groupeId;

    const ok = await this._demarrerMedia(type);
    if (!ok) return;

    this._afficherEcranAppel('appel-groupe', groupeNom);
    this.socket.emit('appel_initier', { groupe_id: groupeId, type });
    const attendreCallId = setInterval(() => {
      if (this.callId) {
        clearInterval(attendreCallId);
        this.enAppel = true;
        this.socket.emit('appel_rejoindre', { call_id: this.callId });
      }
    }, 100);
  },

  // ── Réception d'un appel ─────────────────────────────────────
  _surAppelEntrant(data) {
    if (this.enAppel) {
      // Déjà en appel ailleurs -> on ignore silencieusement (comme un appel manqué)
      return;
    }
    this.callId = data.call_id;
    this.mode = data.mode;
    this.typeAppel = data.type;
    if (data.mode === 'prive') {
      this.autrePartieId = data.appelant_id;
      this.autrePartieNom = data.appelant_nom;
    } else {
      this.groupeId = data.groupe_id;
    }

    const nomAffiche = data.mode === 'prive' ? data.appelant_nom : `${data.appelant_nom} appelle ${data.groupe_nom}`;
    this._jouerSonnerie();
    this._afficherModaleEntrante(nomAffiche, data.type, data.appelant_id);
  },

  async accepterAppel(appelantId) {
    this._arreterSonnerie();
    this._cacherModaleEntrante();

    const ok = await this._demarrerMedia(this.typeAppel);
    if (!ok) {
      this.socket.emit('appel_refuser', { call_id: this.callId, appelant_id: appelantId });
      return;
    }
    this.enAppel = true;
    this._afficherEcranAppel('en-appel', this.mode === 'prive' ? this.autrePartieNom : 'Appel de groupe');
    this.socket.emit('appel_rejoindre', { call_id: this.callId });
  },

  refuserAppel(appelantId) {
    this._arreterSonnerie();
    this._cacherModaleEntrante();
    this.socket.emit('appel_refuser', { call_id: this.callId, appelant_id: appelantId });
    this.callId = null;
  },

  // ── Média local ──────────────────────────────────────────────
  async _demarrerMedia(type) {
    try {
      this.fluxLocal = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: type === 'video' ? { width: 480, height: 360 } : false,
      });
      const videoLocal = document.getElementById('video-locale');
      if (videoLocal && type === 'video') {
        videoLocal.srcObject = this.fluxLocal;
        videoLocal.muted = true;
      }
      return true;
    } catch (err) {
      alert("Impossible d'accéder à la caméra/au micro (permission refusée ?).");
      return false;
    }
  },

  // ── Construction du maillage (mesh) une fois dans la salle ───
  _surParticipants(data) {
    if (data.call_id !== this.callId) return;
    data.participants.forEach(p => this._creerConnexionEtOffrir(p.user_id, p.nom));
  },

  _surNouveauParticipant(data) {
    if (data.call_id !== this.callId) return;
    // On ne fait rien : c'est LUI qui va nous envoyer une offre (voir appel_participants
    // reçu de son côté). On se contente d'afficher son nom dans l'UI si besoin.
    this._ajouterNomParticipant(data.user_id, data.nom);
  },

  async _creerConnexionEtOffrir(autreUserId, autreNom) {
    const pc = this._creerPeerConnection(autreUserId);
    this._ajouterNomParticipant(autreUserId, autreNom);
    const offre = await pc.createOffer();
    await pc.setLocalDescription(offre);
    this.socket.emit('appel_offre', { call_id: this.callId, cible_user_id: autreUserId, sdp: offre });
  },

  _creerPeerConnection(autreUserId) {
    if (this.connexions[autreUserId]) return this.connexions[autreUserId];

    const pc = new RTCPeerConnection(ICE_SERVERS);
    this.connexions[autreUserId] = pc;

    this.fluxLocal.getTracks().forEach(track => pc.addTrack(track, this.fluxLocal));

    pc.onicecandidate = (e) => {
      if (e.candidate) {
        this.socket.emit('appel_ice', { call_id: this.callId, cible_user_id: autreUserId, candidate: e.candidate });
      }
    };

    pc.ontrack = (e) => {
      this._afficherVideoDistante(autreUserId, e.streams[0]);
    };

    pc.onconnectionstatechange = () => {
      if (['failed', 'closed', 'disconnected'].includes(pc.connectionState)) {
        this._retirerParticipant(autreUserId);
      }
    };

    return pc;
  },

  async _surOffre(data) {
    if (data.call_id !== this.callId) return;
    const pc = this._creerPeerConnection(data.de_user_id);
    await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
    const reponse = await pc.createAnswer();
    await pc.setLocalDescription(reponse);
    this.socket.emit('appel_reponse', { call_id: this.callId, cible_user_id: data.de_user_id, sdp: reponse });
  },

  async _surReponse(data) {
    if (data.call_id !== this.callId) return;
    const pc = this.connexions[data.de_user_id];
    if (pc) await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
  },

  async _surIce(data) {
    if (data.call_id !== this.callId) return;
    const pc = this.connexions[data.de_user_id];
    if (pc) {
      try { await pc.addIceCandidate(new RTCIceCandidate(data.candidate)); }
      catch (e) { /* candidat arrivé trop tôt/tard, sans conséquence */ }
    }
  },

  _surParticipantParti(data) {
    if (data.call_id !== this.callId) return;
    this._retirerParticipant(data.user_id);
  },

  _retirerParticipant(userId) {
    const pc = this.connexions[userId];
    if (pc) { pc.close(); delete this.connexions[userId]; }
    const el = this.elementsVideoDistants[userId];
    if (el) { el.parentElement.remove(); delete this.elementsVideoDistants[userId]; }
    if (this.mode === 'prive' && Object.keys(this.connexions).length === 0) {
      this.terminerAppel();
    }
  },

  // ── Terminer ─────────────────────────────────────────────────
  terminerAppel() {
    if (this.callId) this.socket.emit('appel_terminer', { call_id: this.callId });
    this._terminerLocalement();
  },

  _terminerLocalement(message) {
    Object.values(this.connexions).forEach(pc => pc.close());
    this.connexions = {};
    if (this.fluxLocal) {
      this.fluxLocal.getTracks().forEach(t => t.stop());
      this.fluxLocal = null;
    }
    this.elementsVideoDistants = {};
    this.enAppel = false;
    this.callId = null;
    this._arreterSonnerie();
    this._cacherModaleEntrante();
    this._cacherEcranAppel();
    if (message) console.info(message);
  },

  // ── Contrôles pendant l'appel ────────────────────────────────
  basculerMicro() {
    if (!this.fluxLocal) return;
    this.fluxLocal.getAudioTracks().forEach(t => { t.enabled = !t.enabled; });
  },
  basculerCamera() {
    if (!this.fluxLocal) return;
    this.fluxLocal.getVideoTracks().forEach(t => { t.enabled = !t.enabled; });
  },

  // ── UI (fonctions branchées depuis base.html) ───────────────
  _jouerSonnerie() { if (this.sonnerie) { this.sonnerie.loop = true; this.sonnerie.play().catch(() => {}); } },
  _arreterSonnerie() { if (this.sonnerie) { this.sonnerie.pause(); this.sonnerie.currentTime = 0; } },
  _afficherModaleEntrante(nom, type, appelantId) {
    const modale = document.getElementById('modale-appel-entrant');
    if (!modale) return;
    document.getElementById('appel-entrant-nom').textContent = nom;
    document.getElementById('appel-entrant-type').textContent = type === 'video' ? 'Appel vidéo entrant' : 'Appel audio entrant';
    modale.dataset.appelantId = appelantId;
    modale.style.display = 'flex';
  },
  _cacherModaleEntrante() {
    const modale = document.getElementById('modale-appel-entrant');
    if (modale) modale.style.display = 'none';
  },
  _afficherEcranAppel(etat, titre) {
    const ecran = document.getElementById('ecran-appel');
    if (!ecran) return;
    document.getElementById('appel-titre').textContent = titre;
    document.getElementById('appel-statut').textContent =
      etat === 'appel-sortant' ? 'Appel en cours…' : (etat === 'appel-groupe' ? 'Appel de groupe…' : '');
    document.getElementById('video-locale-conteneur').style.display = this.typeAppel === 'video' ? 'block' : 'none';
    ecran.style.display = 'flex';
  },
  _cacherEcranAppel() {
    const ecran = document.getElementById('ecran-appel');
    if (ecran) ecran.style.display = 'none';
    const grille = document.getElementById('grille-video-distantes');
    if (grille) grille.innerHTML = '';
  },
  _afficherVideoDistante(userId, flux) {
    document.getElementById('appel-statut').textContent = '';
    let el = this.elementsVideoDistants[userId];
    if (!el) {
      const conteneur = document.createElement('div');
      conteneur.className = 'appel-video-distante-conteneur';
      if (this.typeAppel === 'video') {
        el = document.createElement('video');
        el.autoplay = true; el.playsInline = true;
      } else {
        el = document.createElement('audio');
        el.autoplay = true;
      }
      conteneur.appendChild(el);
      document.getElementById('grille-video-distantes').appendChild(conteneur);
      this.elementsVideoDistants[userId] = el;
    }
    el.srcObject = flux;
  },
  _ajouterNomParticipant(userId, nom) {
    // Réservé pour un futur affichage de la liste des participants ; pas
    // indispensable au fonctionnement de l'appel lui-même.
  },
};
