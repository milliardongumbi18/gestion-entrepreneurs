// Bascule entre thème clair et sombre, et mémorise le choix sur cet appareil.
// Chargé avec « defer » : il s'exécute une fois la page lue, sans la ralentir.
(function () {
  var bouton = document.getElementById("bascule-theme");
  if (!bouton) return;
  var racine = document.documentElement;

  // Met à jour les informations lues par les lecteurs d'écran.
  function actualiser() {
    var sombre = racine.classList.contains("dark");
    bouton.setAttribute("aria-pressed", sombre ? "true" : "false");
    bouton.setAttribute("aria-label", sombre ? "Passer au thème clair" : "Passer au thème sombre");
  }

  bouton.addEventListener("click", function () {
    var sombre = racine.classList.toggle("dark");
    try {
      localStorage.setItem("theme", sombre ? "sombre" : "clair");
    } catch (e) {
      // Navigation privée : le choix ne sera simplement pas mémorisé.
    }
    actualiser();
  });

  actualiser();
})();