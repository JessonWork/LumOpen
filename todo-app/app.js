// 全局变量
let todos = [];
let currentFilter = 'all';
const todoInput = document.getElementById('todoInput');
const addBtn = document.getElementById('addBtn');
const todoList = document.getElementById('todoList');
const emptyState = document.getElementById('emptyState');
const filterButtons = document.querySelectorAll('.filter-btn');

// 初始化
function init() {
    // 读取本地存储数据
    const savedTodos = localStorage.getItem('todos');
    const savedFilter = localStorage.getItem('currentFilter');
    if (savedTodos) {
        todos = JSON.parse(savedTodos);
    }
    if (savedFilter) {
        currentFilter = savedFilter;
        updateFilterActiveState();
    }
    renderTodos();
    bindEvents();
}

// 绑定事件
function bindEvents() {
    // 输入框内容变化，控制添加按钮是否禁用
    todoInput.addEventListener('input', () => {
        addBtn.disabled = todoInput.value.trim() === '';
    });

    // 点击添加按钮
    addBtn.addEventListener('click', addTodo);

    // 回车添加待办
    todoInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !addBtn.disabled) {
            addTodo();
        }
    });

    // 筛选按钮点击
    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            currentFilter = btn.dataset.filter;
            updateFilterActiveState();
            saveToLocalStorage();
            renderTodos();
        });
    });
}

// 更新筛选按钮激活状态
function updateFilterActiveState() {
    filterButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.filter === currentFilter);
    });
}

// 添加待办
function addTodo() {
    const content = todoInput.value.trim();
    if (!content) return;

    const newTodo = {
        id: Date.now(),
        content: content,
        completed: false
    };

    todos.unshift(newTodo);
    todoInput.value = '';
    addBtn.disabled = true;
    saveToLocalStorage();
    renderTodos();
}

// 切换待办状态
function toggleTodoStatus(id) {
    todos = todos.map(todo => {
        if (todo.id === id) {
            return { ...todo, completed: !todo.completed };
        }
        return todo;
    });
    saveToLocalStorage();
    renderTodos();
}

// 删除待办
function deleteTodo(id) {
    todos = todos.filter(todo => todo.id !== id);
    saveToLocalStorage();
    renderTodos();
}

// 保存到本地存储
function saveToLocalStorage() {
    localStorage.setItem('todos', JSON.stringify(todos));
    localStorage.setItem('currentFilter', currentFilter);
}

// 渲染待办列表
function renderTodos() {
    // 筛选待办
    let filteredTodos = todos;
    if (currentFilter === 'active') {
        filteredTodos = todos.filter(todo => !todo.completed);
    } else if (currentFilter === 'completed') {
        filteredTodos = todos.filter(todo => todo.completed);
    }

    // 渲染列表
    todoList.innerHTML = '';
    if (filteredTodos.length === 0) {
        emptyState.classList.add('show');
        return;
    }
    emptyState.classList.remove('show');

    filteredTodos.forEach(todo => {
        const li = document.createElement('li');
        li.className = `todo-item ${todo.completed ? 'completed' : ''}`;
        li.dataset.id = todo.id;

        li.innerHTML = `
            <div class="status"></div>
            <div class="text">${escapeHtml(todo.content)}</div>
            <button class="delete-btn">🗑️</button>
        `;

        // 点击待办项切换状态
        li.addEventListener('click', (e) => {
            if (!e.target.classList.contains('delete-btn')) {
                toggleTodoStatus(todo.id);
            }
        });

        // 点击删除按钮
        li.querySelector('.delete-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            deleteTodo(todo.id);
        });

        todoList.appendChild(li);
    });
}

// HTML转义，防止XSS
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// 启动应用
document.addEventListener('DOMContentLoaded', init);
