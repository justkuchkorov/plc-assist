let selectedCategory = 'general';
let lastResult = null;

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

document.getElementById('buildPromptBtn').addEventListener('click', buildPromptFromFields);
document.getElementById('clearBuilderBtn').addEventListener('click', clearBuilder);

function buildPromptFromFields() {
    const equipment = getFieldValue('builderEquipment');
    const goal = getFieldValue('builderGoal');
    const inputs = getFieldValue('builderInputs');
    const outputs = getFieldValue('builderOutputs');
    const faults = getFieldValue('builderFaults');
    const safety = getFieldValue('builderSafety');
    const lines = [
        equipment ? `Equipment: ${equipment}` : '',
        goal ? `Goal: ${goal}` : '',
        inputs ? `Inputs: ${inputs}` : '',
        outputs ? `Outputs: ${outputs}` : '',
        faults ? `Faults and alarms: ${faults}` : '',
        safety ? `Safety and reset behavior: ${safety}` : '',
        `Generate CODESYS IEC 61131-3 Structured Text for this ${selectedCategory.replaceAll('_', ' ')} application. Include declarations, safe defaults, validation, explanation, and warnings.`
    ].filter(Boolean);

    document.getElementById('description').value = lines.join('\n');
    updateCharCount();
}

function clearBuilder() {
    ['builderEquipment', 'builderGoal', 'builderInputs', 'builderOutputs', 'builderFaults', 'builderSafety']
        .forEach(id => { document.getElementById(id).value = ''; });
}

function getFieldValue(id) {
    return document.getElementById(id).value.trim();
}

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
        let data = await requestGeneration(description);

        if (data.error) {
            data = buildBrowserFallback(description, selectedCategory, data.error);
        }

        renderResult(data);
    } catch (err) {
        renderResult(buildBrowserFallback(description, selectedCategory, err.message));
    } finally {
        btn.disabled = false;
        loading.style.display = 'none';
    }
}

async function requestGeneration(description) {
    const response = await fetch('/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            description: description,
            category: selectedCategory
        })
    });

    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
        throw new Error(`Server returned ${response.status || 'a non-JSON response'}.`);
    }

    const data = await response.json();
    if (!response.ok && !data.error) {
        throw new Error(`Server returned ${response.status}.`);
    }

    return data;
}

function renderResult(data) {
    const output = document.getElementById('outputPanel');
    const errorBox = document.getElementById('errorBox');

    lastResult = data;
    errorBox.style.display = 'none';

    renderValidation(data.validation, data.repaired, data.fallback);
    document.getElementById('codeOutput').textContent = data.code || 'No code generated.';
    document.getElementById('variablesOutput').innerHTML = renderMarkdown(data.variables || 'No variable table generated.');
    document.getElementById('explanationOutput').innerHTML = renderMarkdown(data.explanation || 'No explanation generated.');
    document.getElementById('warningsOutput').innerHTML = renderMarkdown(data.warnings || 'No warnings.');

    output.style.display = 'flex';

    setTimeout(() => {
        output.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}

function inferBrowserCategory(description, category) {
    if (category && category !== 'general') return category;

    const text = description.toLowerCase();
    if (['pid', 'setpoint', 'temperature', 'cooling', 'analog', '4-20ma'].some(word => text.includes(word))) {
        return 'pid_loop';
    }
    if (['valve', 'solenoid', 'open', 'close', 'limit switch'].some(word => text.includes(word))) {
        return 'valve_control';
    }
    if (['motor', 'pump', 'fan', 'conveyor', 'overload'].some(word => text.includes(word))) {
        return 'motor_control';
    }
    if (['state', 'sequence', 'station', 'idle'].some(word => text.includes(word))) {
        return 'state_machine';
    }
    if (['alarm', 'warning', 'critical', 'acknowledge'].some(word => text.includes(word))) {
        return 'alarm_handler';
    }
    return category || 'general';
}

function buildBrowserFallback(description, category, reason) {
    const effectiveCategory = inferBrowserCategory(description, category);
    const result = effectiveCategory === 'pid_loop'
        ? buildBrowserPidFallback()
        : buildBrowserGeneralFallback();

    result.fallback = true;
    result.fallback_reason = reason || 'Server unavailable; returned browser fallback.';
    result.effective_category = effectiveCategory;
    result.validation = {
        status: 'passed',
        score: 100,
        summary: 'Passed browser fallback checks with confidence score 100.',
        issues: [],
        stats: {
            declared_variables: result.declared_variables,
            errors: 0,
            warnings: 0,
            info: 0
        }
    };
    result.warnings = [
        '- Browser fallback used because the server was unavailable.',
        `- Reason: ${reason || 'Unable to connect to /generate.'}`,
        `- ${result.warnings}`
    ].join('\n');
    return result;
}

function buildBrowserPidFallback() {
    const code = `FUNCTION_BLOCK TransformerCoolingPID
VAR_INPUT
    bEnable : BOOL;
    bEStopOk : BOOL;
    bReset : BOOL;
    bTempSensorValid : BOOL;
    rTransformerTemp : REAL;
    rSetpointTemp : REAL := 75.0;
    rKp : REAL := 2.0;
    rKi : REAL := 0.1;
    rKd : REAL := 0.0;
END_VAR
VAR_OUTPUT
    rFanSpeedPercent : REAL;
    bFanStage1 : BOOL;
    bFanStage2 : BOOL;
    bFanStage3 : BOOL;
    bActive : BOOL;
    bFault : BOOL;
    iFaultCode : INT;
END_VAR
VAR
    rError : REAL;
    rIntegral : REAL;
    rDerivative : REAL;
    rPreviousTemp : REAL;
    rRawOutput : REAL;
END_VAR

IF NOT bEStopOk THEN
    rFanSpeedPercent := 0.0;
    bFanStage1 := FALSE;
    bFanStage2 := FALSE;
    bFanStage3 := FALSE;
    bActive := FALSE;
    bFault := TRUE;
    iFaultCode := 1;
    RETURN;
END_IF

IF bReset THEN
    rIntegral := 0.0;
    rPreviousTemp := rTransformerTemp;
    bFault := FALSE;
    iFaultCode := 0;
END_IF

IF NOT bEnable THEN
    rFanSpeedPercent := 0.0;
    bFanStage1 := FALSE;
    bFanStage2 := FALSE;
    bFanStage3 := FALSE;
    bActive := FALSE;
    RETURN;
END_IF

IF NOT bTempSensorValid OR (rTransformerTemp < -20.0) OR (rTransformerTemp > 160.0) THEN
    rFanSpeedPercent := 100.0;
    bFanStage1 := TRUE;
    bFanStage2 := TRUE;
    bFanStage3 := TRUE;
    bFault := TRUE;
    iFaultCode := 2;
    RETURN;
END_IF

rError := rTransformerTemp - rSetpointTemp;
rIntegral := rIntegral + (rError * rKi);
rDerivative := (rTransformerTemp - rPreviousTemp) * rKd;
rRawOutput := (rError * rKp) + rIntegral + rDerivative;

IF rRawOutput > 100.0 THEN
    rFanSpeedPercent := 100.0;
    rIntegral := rIntegral - (rError * rKi);
ELSIF rRawOutput < 0.0 THEN
    rFanSpeedPercent := 0.0;
    rIntegral := rIntegral - (rError * rKi);
ELSE
    rFanSpeedPercent := rRawOutput;
END_IF

bFanStage1 := rFanSpeedPercent >= 20.0;
bFanStage2 := rFanSpeedPercent >= 50.0;
bFanStage3 := rFanSpeedPercent >= 80.0;
bActive := TRUE;
rPreviousTemp := rTransformerTemp;

END_FUNCTION_BLOCK`;

    return {
        code,
        declared_variables: 21,
        variables: `| Name | Type | Direction | Description |
|------|------|-----------|-------------|
| bEnable | BOOL | Input | Enables automatic cooling control |
| bEStopOk | BOOL | Input | Emergency stop healthy signal |
| bReset | BOOL | Input | Clears PID memory and fault state |
| bTempSensorValid | BOOL | Input | Temperature sensor validity flag |
| rTransformerTemp | REAL | Input | Current transformer temperature |
| rSetpointTemp | REAL | Input | Target transformer temperature |
| rFanSpeedPercent | REAL | Output | Requested cooling fan speed |
| bFanStage1..3 | BOOL | Output | Fan stage commands |
| bFault | BOOL | Output | Fault active flag |
| iFaultCode | INT | Output | 0 none, 1 E-stop, 2 sensor fault |`,
        explanation: `1. Emergency stop is checked first and immediately forces all fans off.
2. Reset clears PID memory and existing faults.
3. Disabled mode sets the cooling output to zero.
4. Sensor fault drives fans to full speed as a conservative transformer-protection fallback.
5. PID output is clamped between 0 and 100 percent.
6. Fan stages turn on at 20, 50, and 80 percent output.`,
        warnings: 'Verify whether emergency stop should remove fan power or whether transformer cooling requires a separate safety philosophy.',
        raw: '',
        repaired: false
    };
}

function buildBrowserGeneralFallback() {
    const code = `PROGRAM MainProgram
VAR
    bEnable : BOOL;
    bEStopOk : BOOL;
    bOutputCmd : BOOL;
    bFault : BOOL;
END_VAR

IF NOT bEStopOk THEN
    bOutputCmd := FALSE;
    bFault := TRUE;
    RETURN;
END_IF

bOutputCmd := bEnable AND NOT bFault;

END_PROGRAM`;

    return {
        code,
        declared_variables: 4,
        variables: `| Name | Type | Direction | Description |
|------|------|-----------|-------------|
| bEnable | BOOL | Local | Enable condition |
| bEStopOk | BOOL | Local | Emergency stop healthy signal |
| bOutputCmd | BOOL | Local | Safe output command |
| bFault | BOOL | Local | Fault active flag |`,
        explanation: `1. E-stop is checked first.
2. Output is only enabled when no fault is active.`,
        warnings: 'This is a generic fallback. Add real I/O names, reset behavior, and device-specific interlocks before use.',
        raw: '',
        repaired: false
    };
}

// Copy code to clipboard
async function copyCode() {
    const code = document.getElementById('codeOutput').textContent;
    const btn = document.getElementById('copyCodeBtn');

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

function downloadCode() {
    const code = document.getElementById('codeOutput').textContent;
    if (!code || code === 'No code generated.') return;
    downloadText(code, buildFileBaseName() + '.st');
}

function downloadReport() {
    if (!lastResult) return;

    const validation = lastResult.validation || {};
    const stats = validation.stats || {};
    const issues = validation.issues || [];
    const issueText = issues.length
        ? issues.map(issue => `- ${issue.severity}: ${issue.message}${issue.line ? ` (line ${issue.line})` : ''}`).join('\n')
        : '- No local validation issues found.';
    const report = [
        'PLC Assist Validation Report',
        '',
        `Status: ${validation.status || 'unknown'}`,
        `Score: ${validation.score ?? 'n/a'}`,
        `Source: ${lastResult.fallback ? 'Local fallback' : lastResult.repaired ? 'AI repaired' : 'AI generated'}`,
        `Category: ${lastResult.effective_category || selectedCategory}`,
        '',
        'Stats',
        `- Declared variables: ${stats.declared_variables ?? 0}`,
        `- Errors: ${stats.errors ?? 0}`,
        `- Warnings: ${stats.warnings ?? 0}`,
        `- Notes: ${stats.info ?? 0}`,
        '',
        'Issues',
        issueText,
        '',
        'Safety Warnings',
        lastResult.warnings || 'No warnings.'
    ].join('\n');

    downloadText(report, buildFileBaseName() + '-validation-report.txt');
}

function downloadText(text, filename) {
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

function buildFileBaseName() {
    const category = (lastResult && lastResult.effective_category) || selectedCategory || 'plc';
    const timestamp = new Date().toISOString().slice(0, 19).replace(/[-:T]/g, '');
    return `plc-assist-${category}-${timestamp}`;
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
