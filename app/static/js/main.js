// Auto-dismiss alerts after a while
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.alert').forEach((el) => {
    setTimeout(() => {
      const alert = bootstrap.Alert.getOrCreateInstance(el);
      if (alert) alert.close();
    }, 6000);
  });
});
