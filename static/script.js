let selectedCategory = 'general';

// Category selection
function selectCategory(id) {
    selectedCategory = id;
    document.querySelectorAll('.cat-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.category === id);
    });
}

// Load example for selected category
function loadExample() {
    const example = EXAMPLES[selectedCategory];
    if (example) {
        document.getElementById('description').value = example;
        updateCharCount();
    }
}

function loadIdea(category, description) {
    selectCategory(category);
    document.getElementById('description').value = description;
    updateCharCount();
}

document.querySelectorAll('.idea-chip').forEach(btn => {
    btn.addEventListener('click', () => {
        loadIdea(btn.dataset.category, btn.dataset.description);
    });
});

// Character counter
const textarea = document.getElementById('description');
textarea.addEventListener('input', updateCharCount);

function updateCharCount() {
    const count = textarea.value.length;
    document.getElementById('charCount').textContent = `${count} chars`;
}

// Generate code
async function generate() {
    const description = document.getElementById('description').value.trim();
    if (!description) {
        showError('Please describe the control logic you need.');
        return;
    }

    const btn = document.getElementById('generateBtn');
    const loading = document.getElementById('loading');
    const output = document.getElementById('outputPanel');
    const errorBox = document.getElementById('errorBox');

    // Show loading
    btn.disabled = true;
    loading.style.display = 'flex';
    output.style.display = 'none';
    errorBox.style.display = 'none';

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                description: description,
                category: selectedCategory
            })
        });

        const data = await response.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        // Populate output
        renderValidation(data.validation, data.repaired, data.fallback);
        document.getElementById('codeOutput').textContent = data.code || 'No code generated.';
        document.getElementById('variablesOutput').innerHTML = renderMarkdown(data.variables || 'No variable table generated.');
        document.getElementById('explanationOutput').innerHTML = renderMarkdown(data.explanation || 'No explanation generated.');
        document.getElementById('warningsOutput').innerHTML = renderMarkdown(data.warnings || 'No warnings.');

        output.style.display = 'flex';

        // Scroll to output
        setTimeout(() => {
            output.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);

    } catch (err) {
        showError('Failed to connect to the server. Make sure it\'s running.');
    } finally {
        btn.disabled = false;
        loading.style.display = 'none';
    }
}

// Copy code to clipboard
async function copyCode() {
    const code = document.getElementById('codeOutput').textContent;
    const btn = document.querySelector('.copy-btn');

    try {
        await navigator.clipboard.writeText(code);
        btn.classList.add('copied');
        btn.innerHTML = '<span class="material-icons-outlined">check</span> Copied!';
        setTimeout(() => {
            btn.classList.remove('copied');
            btn.innerHTML = '<span class="material-icons-outlined">content_copy</span> Copy';
        }, 2000);
    } catch {
        // Fallback
        const ta = document.createElement('textarea');
        ta.value = code;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        btn.innerHTML = '<span class="material-icons-outlined">check</span> Copied!';
        setTimeout(() => {
            btn.innerHTML = '<span class="material-icons-outlined">content_copy</span> Copy';
        }, 2000);
    }
}

// Show error
function showError(message) {
    const errorBox = document.getElementById('errorBox');
    document.getElementById('errorText').textContent = message;
    errorBox.style.display = 'flex';
}

// Render local validation results
function renderValidation(validation, repaired, fallback) {
    const section = document.getElementById('validationSection');
    const icon = document.getElementById('validationIcon');
    const score = document.getElementById('validationScore');
    const output = document.getElementById('validationOutput');

    if (!validation) {
        section.style.display = 'none';
        return;
    }

    const status = validation.status || 'needs_repair';
    section.style.display = 'block';
    section.classList.remove('passed', 'passed-with-warnings', 'needs-repair');
    section.classList.add(status.replaceAll('_', '-'));

    icon.textContent = status === 'passed' ? 'verified' : status === 'passed_with_warnings' ? 'rule' : 'report';
    score.textContent = `Score ${validation.score ?? 0}`;

    const stats = validation.stats || {};
    const issues = validation.issues || [];
    const badges = [];
    if (repaired || validation.repaired) {
        badges.push('<span class="validation-badge repaired">Auto-repaired</span>');
    }
    if (fallback) {
        badges.push('<span class="validation-badge fallback">Local fallback</span>');
    }

    const issueHtml = issues.length
        ? `<div class="validation-issues">${issues.map(renderValidationIssue).join('')}</div>`
        : '<p class="validation-empty">No local validation issues found.</p>';

    output.innerHTML = `
        <div class="validation-summary-row">
            <p>${escapeHtml(validation.summary || 'Validation completed.')}</p>
            <div class="validation-badges">${badges.join('')}</div>
        </div>
        <div class="validation-stats">
            <span>${stats.declared_variables ?? 0} declared vars</span>
            <span>${stats.errors ?? 0} errors</span>
            <span>${stats.warnings ?? 0} warnings</span>
            <span>${stats.info ?? 0} notes</span>
        </div>
        ${issueHtml}
    `;
}

function renderValidationIssue(issue) {
    const line = issue.line ? `Line ${issue.line}` : issue.code;
    return `
        <div class="validation-issue ${escapeHtml(issue.severity || 'info')}">
            <span class="issue-severity">${escapeHtml(issue.severity || 'info')}</span>
            <div>
                <strong>${escapeHtml(line)}</strong>
                <p>${escapeHtml(issue.message || '')}</p>
            </div>
        </div>
    `;
}

// Simple markdown renderer (handles tables, lists, bold, code)
function renderMarkdown(text) {
    if (!text) return '';

    // Handle tables
    if (text.includes('|')) {
        const lines = text.split('\n');
        let html = '';
        let inTable = false;
        let isHeader = true;

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();

            if (line.startsWith('|') && line.endsWith('|')) {
                // Skip separator row
                if (line.match(/^\|[\s\-:|]+\|$/)) {
                    continue;
                }

                if (!inTable) {
                    html += '<table>';
                    inTable = true;
                    isHeader = true;
                }

                const cells = line.split('|').filter(c => c.trim() !== '');
                const tag = isHeader ? 'th' : 'td';
                html += '<tr>';
                cells.forEach(cell => {
                    html += `<${tag}>${escapeHtml(cell.trim())}</${tag}>`;
                });
                html += '</tr>';
                isHeader = false;
            } else {
                if (inTable) {
                    html += '</table>';
                    inTable = false;
                }
                html += renderLine(line);
            }
        }

        if (inTable) html += '</table>';
        return html;
    }

    // Handle regular text
    return text.split('\n').map(renderLine).join('');
}

function renderLine(line) {
    if (!line.trim()) return '';

    // Numbered list
    if (line.match(/^\d+\.\s/)) {
        const content = line.replace(/^\d+\.\s/, '');
        return `<p style="padding-left: 16px;">${formatInline(content)}</p>`;
    }

    // Bullet list
    if (line.match(/^[-*]\s/)) {
        const content = line.replace(/^[-*]\s/, '');
        return `<p style="padding-left: 16px;">${formatInline('- ' + content)}</p>`;
    }

    return `<p>${formatInline(line)}</p>`;
}

function formatInline(text) {
    // Bold
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Inline code
    text = text.replace(/`(.*?)`/g, '<code>$1</code>');
    return text;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Keyboard shortcut: Ctrl+Enter to generate
textarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        generate();
    }
});
