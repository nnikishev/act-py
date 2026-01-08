// Основной JavaScript файл

$(document).ready(function() {
    // Инициализация тултипов Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Инициализация попапов
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Подтверждение удаления
    $('.confirm-delete').on('click', function(e) {
        if (!confirm('Вы уверены, что хотите удалить этот элемент?')) {
            e.preventDefault();
            return false;
        }
        return true;
    });

    // Копирование в буфер обмена
    $('.copy-to-clipboard').on('click', function() {
        var text = $(this).data('clipboard-text');
        navigator.clipboard.writeText(text).then(function() {
            // Показываем уведомление об успехе
            showToast('Скопировано в буфер обмена!', 'success');
        }, function(err) {
            showToast('Ошибка копирования', 'error');
        });
    });

    // Плавная прокрутка
    $('a[href^="#"]').on('click', function(event) {
        if (this.hash !== "") {
            event.preventDefault();
            var hash = this.hash;
            $('html, body').animate({
                scrollTop: $(hash).offset().top - 70
            }, 800);
        }
    });

    // Автоматическое скрытие алертов через 5 секунд
    setTimeout(function() {
        $('.alert:not(.alert-permanent)').fadeTo(500, 0).slideUp(500, function() {
            $(this).remove();
        });
    }, 5000);

    // Валидация форм
    $('form.needs-validation').on('submit', function(event) {
        if (!this.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        $(this).addClass('was-validated');
    });

    // Подсветка обязательных полей
    $('.required input, .required select, .required textarea').on('blur', function() {
        if (!$(this).val()) {
            $(this).addClass('is-invalid');
        } else {
            $(this).removeClass('is-invalid');
        }
    });

    // Автоматический расчет суммы
    $('.calculate').on('input', function() {
        var quantity = parseFloat($(this).closest('.row').find('.quantity').val()) || 0;
        var price = parseFloat($(this).closest('.row').find('.price').val()) || 0;
        var total = quantity * price;
        $(this).closest('.row').find('.total').val(total.toFixed(2));
        calculateGrandTotal();
    });

    // Функция для показа тостов
    function showToast(message, type = 'info') {
        // Создаем контейнер для тостов если его нет
        if (!$('#toast-container').length) {
            $('body').append('<div id="toast-container" class="toast-container position-fixed bottom-0 end-0 p-3"></div>');
        }

        var bgClass = '';
        switch(type) {
            case 'success': bgClass = 'bg-success'; break;
            case 'error': bgClass = 'bg-danger'; break;
            case 'warning': bgClass = 'bg-warning'; break;
            default: bgClass = 'bg-info';
        }

        var toastId = 'toast-' + Date.now();
        var toastHtml = `
            <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header ${bgClass} text-white">
                    <strong class="me-auto">Уведомление</strong>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;

        $('#toast-container').append(toastHtml);
        var toast = new bootstrap.Toast(document.getElementById(toastId));
        toast.show();

        // Удаляем toast после скрытия
        document.getElementById(toastId).addEventListener('hidden.bs.toast', function () {
            $(this).remove();
        });
    }

    // Глобальная функция для показа тостов
    window.showToast = showToast;

    // Загрузка файлов с прогрессом
    $('input[type="file"]').on('change', function() {
        var fileName = $(this).val().split('\\').pop();
        $(this).next('.custom-file-label').html(fileName);
    });

    // Переключение темы
    $('#themeToggle').on('click', function() {
        var currentTheme = document.documentElement.getAttribute('data-bs-theme');
        var newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-bs-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        $(this).find('i').toggleClass('bi-moon bi-sun');
    });

    // Проверка сохраненной темы
    var savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-bs-theme', savedTheme);
    if (savedTheme === 'dark') {
        $('#themeToggle i').removeClass('bi-moon').addClass('bi-sun');
    }

    // AJAX загрузка контента
    $('.ajax-load').on('click', function(e) {
        e.preventDefault();
        var url = $(this).attr('href');
        var target = $(this).data('target');
        
        $(target).addClass('loading');
        
        $.ajax({
            url: url,
            type: 'GET',
            success: function(data) {
                $(target).html(data).removeClass('loading');
            },
            error: function() {
                $(target).html('<div class="alert alert-danger">Ошибка загрузки</div>').removeClass('loading');
            }
        });
    });

    // Автоматическое сохранение формы
    var saveTimeout;
    $('form.auto-save input, form.auto-save textarea, form.auto-save select').on('input change', function() {
        clearTimeout(saveTimeout);
        saveTimeout = setTimeout(function() {
            $('form.auto-save').submit();
        }, 2000);
    });
});

// Функция для расчета общей суммы
function calculateGrandTotal() {
    var grandTotal = 0;
    $('.total').each(function() {
        grandTotal += parseFloat($(this).val()) || 0;
    });
    $('#grandTotal').text(grandTotal.toFixed(2));
}

// Функция для форматирования чисел
function formatNumber(number) {
    return new Intl.NumberFormat('ru-RU', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(number);
}

// Функция для форматирования даты
function formatDate(dateString) {
    var date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

// Экспорт функций в глобальную область видимости
window.formatNumber = formatNumber;
window.formatDate = formatDate;
window.calculateGrandTotal = calculateGrandTotal;