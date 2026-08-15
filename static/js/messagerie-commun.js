/* ============================================================
   SmartLife AI — Messagerie : émojis + messages vocaux
   Utilisé par templates/messagerie/prive.html et groupe.html
   ============================================================ */

const EMOJIS_COURANTS = [
  '😀','😂','😍','😊','😉','😢','😭','😡','👍','👎',
  '🙏','👏','🔥','❤️','💔','🎉','😴','🤔','😱','🙌',
  '✅','❌','📚','✍️','💡','⏰','📌','🎓','☕','💪',
];

function initEmojiPicker(boutonId, panneauId, inputEl) {
  const bouton = document.getElementById(boutonId);
  const panneau = document.getElementById(panneauId);
  if (!bouton || !panneau) return;

  panneau.innerHTML = EMOJIS_COURANTS
    .map(e => `<button type="button" class="msg-emoji-item">${e}</button>`)
    .join('');

  bouton.addEventListener('click', (e) => {
    e.stopPropagation();
    panneau.classList.toggle('ouvert');
  });

  panneau.querySelectorAll('.msg-emoji-item').forEach(item => {
    item.addEventListener('click', () => {
      const debut = inputEl.selectionStart ?? inputEl.value.length;
      const fin = inputEl.selectionEnd ?? inputEl.value.length;
      inputEl.value = inputEl.value.slice(0, debut) + item.textContent + inputEl.value.slice(fin);
      inputEl.focus();
      inputEl.selectionStart = inputEl.selectionEnd = debut + item.textContent.length;
    });
  });

  document.addEventListener('click', (e) => {
    if (!panneau.contains(e.target) && e.target !== bouton) {
      panneau.classList.remove('ouvert');
    }
  });
}

function initEnregistrementVocal({ boutonId, indicateurId, boutonStopId, boutonAnnulerId, urlEnvoi, csrfToken }) {
  const bouton = document.getElementById(boutonId);
  const indicateur = document.getElementById(indicateurId);
  const boutonStop = document.getElementById(boutonStopId);
  const boutonAnnuler = document.getElementById(boutonAnnulerId);
  if (!bouton) return;

  let mediaRecorder = null;
  let morceaux = [];
  let flux = null;

  async function demarrer() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      alert("L'enregistrement vocal n'est pas supporté par ce navigateur.");
      return;
    }
    try {
      flux = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      alert("Impossible d'accéder au micro (permission refusée ?).");
      return;
    }
    morceaux = [];
    mediaRecorder = new MediaRecorder(flux);
    mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) morceaux.push(e.data); };
    mediaRecorder.start();
    indicateur.style.display = 'flex';
    bouton.classList.add('actif');
  }

  function arreterFlux() {
    if (flux) flux.getTracks().forEach(t => t.stop());
    indicateur.style.display = 'none';
    bouton.classList.remove('actif');
  }

  async function envoyer() {
    if (!mediaRecorder) return;
    mediaRecorder.onstop = async () => {
      const blob = new Blob(morceaux, { type: 'audio/webm' });
      const fd = new FormData();
      fd.append('csrf_token', csrfToken);
      fd.append('contenu', '');
      fd.append('fichier', blob, 'message-vocal.webm');
      arreterFlux();
      try {
        await fetch(urlEnvoi, { method: 'POST', body: fd });
      } catch (err) {
        alert("L'envoi du message vocal a échoué. Réessaie.");
      }
    };
    mediaRecorder.stop();
  }

  function annuler() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.onstop = null;
      mediaRecorder.stop();
    }
    arreterFlux();
  }

  bouton.addEventListener('click', () => {
    if (!mediaRecorder || mediaRecorder.state === 'inactive') demarrer();
  });
  if (boutonStop) boutonStop.addEventListener('click', envoyer);
  if (boutonAnnuler) boutonAnnuler.addEventListener('click', annuler);
}
