allCsvRows = [];

function readFile(){
  let fileInput = document.getElementById("fileInput");
  let fileContentDiv = document.getElementById("fileContent");
  const file = fileInput.files[0];
  window.formData = new FormData();
  formData.append('file', file);
  if (file.type === "text/csv") {
    handleFile(file, fileContentDiv);
  }else {
    fileContentDiv.textContent = "Неподдерживаемый формат файла";
  }
}

function handleFile(file, fileContentDiv) {
  const reader = new FileReader();
  reader.onload = function (e) {
    const csvContent = e.target.result;
    const lines = csvContent.split("\n");
    // Очищаем массив перед добавлением новых строк
    allCsvRows = [];

    lines.forEach((line) => {
      const columns = line.split(",");
      allCsvRows.push(columns);
    });

    // Ограничение на количество столбцов и строк
    const maxColumns = 5; // 5 столбцов в начале и 5 столбцов в конце
    const maxRows = 11;    // 10 строк в начале и 10 строк в конце

    // Создаем элемент таблицы и вставляем содержимое CSV
    const table = document.createElement("table");

    lines.forEach((line, rowIndex) => {
      if (rowIndex < maxRows || rowIndex >= lines.length - maxRows) {
        const row = document.createElement("tr");
        const columns = line.split(",");

        columns.forEach((column, columnIndex) => {
          if (columnIndex < maxColumns || columnIndex >= columns.length - maxColumns) {
            const cell = document.createElement("td");
            cell.textContent = column;
            row.appendChild(cell);
          }
        });

        table.appendChild(row);

        if (rowIndex === 0) {
          row.querySelectorAll("td").forEach((cell) => {
            cell.style.fontWeight = "bold";
          });
        }

        if (rowIndex % 2 === 0) {
          row.classList.add("gray-row");
        }
        }
      });

      table.classList.add("table"); // Добавляем класс "table" к таблице
      fileContentDiv.innerHTML = ""; // Очищаем предыдущее содержимое
      fileContentDiv.appendChild(table);
    };
    reader.readAsText(file);
}


// Функция поиска строки
function searchTable() {
  const input = document.getElementById("searchInput").value.toLowerCase();
  const searchResult = document.getElementById("searchResult");

  let foundRow = null;

  if (!isNaN(input) && input >= 1 && input <= 20) {
    searchResult.textContent = "Сам найди эту строчку, это не сложно!";
    return;
  }

  // Ищем первую подходящую строку
  allCsvRows.forEach((row) => {
    row.forEach((cell) => {
      if (cell.toLowerCase().includes(input)) {
        foundRow = row;
        return;
      }
    });
    if (foundRow) {
      return;
    }
  });

  if (foundRow) {
    const resultTable = document.createElement("table");
    resultTable.classList.add("table"); // Добавляем класс "table" к таблице

    const maxColumns = 5; // Ограничение на количество столбцов

    // Создаем первую строку (названия столбцов)
    const headerRow = document.createElement("tr");
    const headerCells = allCsvRows[0];
    for (let j = 0; j < headerCells.length; j++) {
      if (j < maxColumns || j >= headerCells.length - maxColumns) {
        const headerCell = document.createElement("td");
        headerCell.textContent = headerCells[j];
        headerCell.style.fontWeight = "bold";
        headerRow.appendChild(headerCell);
      }
    }
    resultTable.appendChild(headerRow);

    // Создаем найденную строку
    const row = document.createElement("tr");
    for (let i = 0; i < foundRow.length; i++) {
      if (i < maxColumns || i >= foundRow.length - maxColumns) {
        const cell = document.createElement("td");
        cell.textContent = foundRow[i];
        row.appendChild(cell);
      }
    }
    resultTable.appendChild(row);

    searchResult.innerHTML = ""; // Очищаем предыдущее содержимое
    searchResult.appendChild(resultTable);
  } else {
    searchResult.textContent = "Ничего не найдено";
  }
}


async function fetchFile() {
  let pathname = document.location.pathname;
  if (pathname !== undefined) {
    pathname = pathname.split('/')
    if (pathname.length > 0)
      pathname = pathname.slice(-1)[0];
  }
  if (pathname == 'get_answer.html') {
    console.log('Тут сейчас будем фечить csv с бэка и  отрисовывать ее');
    const backendUrl = 'http://127.0.0.1:8000';
    //запихиваем ответ в файловый объект и парсим его и вставляем в html
    try {
      const response = await fetch(backendUrl + '/get_file');
      console.log(response);
      if (response.ok) {
        const blob = await response.blob();
        const fileContentDiv = document.getElementById('fileContent');
        handleFile(blob, fileContentDiv);
        //Загружаем график зависмости срыва/не срыва
        try {
          const response = await fetch(backendUrl + '/get_distribution_schedule');
          if (response.ok) {
            const responseData = await response.json();
            const base64Image = responseData.image;
            const imageUrl = `data:image/png;base64,${base64Image}`;
            distributionSchedule.src = imageUrl;
          } else {
            console.error("Ошибка при получении графика");
          }
        } catch (error) {
          console.error("Произошла ошибка при отправке запроса:", error);
        }
        //Загрузка графика зависимости сумм
        try {
          const response = await fetch(backendUrl + '/get_distributio_sums');
          if (response.ok) {
            const responseData = await response.json();
            const base64Image = responseData.image;
            const imageUrl = `data:image/png;base64,${base64Image}`;
            distributionSums.src = imageUrl;
          } else {
            console.error("Ошибка при получении графика");
          }
        } catch (error) {
          console.error("Произошла ошибка при отправке запроса:", error);
        }
        //Загрузка графика уверенности модели
        try {
          const response = await fetch(backendUrl + '/get_distribution_probability');
          if (response.ok) {
            const responseData = await response.json();
            const base64Image = responseData.image;
            const imageUrl = `data:image/png;base64,${base64Image}`;
            distributionPro.src = imageUrl;
          } else {
            console.error("Ошибка при получении графика");
          }
        } catch (error) {
          console.error("Произошла ошибка при отправке запроса:", error);
        }


      } else {
        console.error("Ошибка");
      }
    } catch (error) {
      // Обработка других ошибок, которые могли возникнуть при запросе
      console.error("Произошла ошибка при отправке запроса:", error);
    }

  } else {
    console.log('Тут мы ничего не делаем');
  }
}


document.addEventListener("DOMContentLoaded", fetchFile);

document.getElementById("get_answer").addEventListener("click", async function() {
  const backendUrl = 'http://127.0.0.1:8000';
  let response = await fetch(backendUrl + '/upload', {
    method: 'POST',
    body: window.formData
  });
  if (response.task = "complite"){
    window.location.href = "get_answer.html";
  }
  else{
    console.log(response);
  }
});

// Download

document.getElementById("downloadButton").addEventListener("click", async function() {
  const backendUrl = 'http://127.0.0.1:8000/get_file';

  // Отправка запрос на скачивание файла
  try {
      const response = await fetch(backendUrl);
      if (response.ok) {
          // Получение данные файла
          const blob = await response.blob();
          
          // Создайём временную ссылку для скачивания файла
          const url = window.URL.createObjectURL(blob);
          
          // Создаём ссылку для скачивания
          const a = document.createElement("a");
          a.href = url;
          a.download = "resultdata.csv"; // Задайте имя файла
          document.body.appendChild(a);
          a.click();
          
          // Удаляем ссылку после скачивания
          window.URL.revokeObjectURL(url);
      } else {
          // Валидация ошибки, если файл не найден
          console.error("Ошибка: файл не найден");
      }
  } catch (error) {
      // Валидация других ошибок, возникших при запросе
      console.error("Произошла ошибка при отправке запроса:", error);
  }
});



var button = document.getElementById("redirectButton");

button.addEventListener("click", function() {
  // Перенаправляем пользователя на другую страницу
  window.location.href = "InterML.html";
});



// Проверяем, есть ли у пользователя юзер токен
document.addEventListener('DOMContentLoaded', function () {
  // Проверяем наличие юзер токена в куки
  const userToken = getCookie('userToken');

  if (userToken) {
    // Юзер токен существует - пользователь зарегистрирован
    console.log('User is authenticated');
  } else {
    // Юзер токен отсутствует - перенаправляем на страницу регистрации
    window.location.href = 'reg.html';
  }

  // Функция для извлечения куки по имени
  function getCookie(name) {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.startsWith(name + '=')) {
        return cookie.substring(name.length + 1);
      }
    }
    return null;
  }
});