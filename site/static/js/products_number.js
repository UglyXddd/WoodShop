function updateCartCount() {
    const cartCountElem = document.getElementById('cart-count'); // Элемент для отображения количества товаров

    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    let itemCount = 0; // Переменная для хранения количества товаров

    cart.forEach(item => {
        itemCount += item.quantity; // Увеличиваем количество товаров
    });

    if (cartCountElem) {
        cartCountElem.textContent = itemCount; // Обновляем количество товаров на иконке
    }
}

// Обновляем количество товаров при загрузке страницы
document.addEventListener('DOMContentLoaded', updateCartCount);