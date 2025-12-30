frappe.pages['chatbot'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'AI Chatbot',
        single_column: true
    });

    // Initialize chatbot
    new ERPNextChatbot(page);
};

class ERPNextChatbot {
    constructor(page) {
        this.page = page;
        this.session_id = null;
        this.poll_interval = null;
        this.last_message_time = null;
        this.is_waiting_response = false;
        this.charts = {}; // Track chart instances by message ID

        this.init();
    }

    init() {
        // Load HTML template
        $(this.page.body).html(frappe.render_template('chatbot'));

        // Bind events
        this.bind_events();

        // Load existing sessions
        this.load_sessions();
    }

    bind_events() {
        const self = this;

        // New session button
        $('#new-session-btn').on('click', () => this.create_session());

        // Send message
        $('#send-btn').on('click', () => this.send_message());

        // Enter key to send
        $('#message-input').on('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                self.send_message();
            }
        });

        // Auto-resize textarea
        $('#message-input').on('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });

        // Close session
        $('#close-session-btn').on('click', () => this.close_session());
    }

    async load_sessions() {
        try {
            const response = await frappe.call({
                method: 'erpnext_chatbot.api.chat.get_sessions',
                args: { status: 'Active', limit: 20 }
            });

            if (response.message && response.message.success) {
                this.render_sessions(response.message.message.sessions);

                // Auto-select first active session
                if (response.message.message.sessions.length > 0) {
                    this.select_session(response.message.message.sessions[0].session_id);
                }
            }
        } catch (error) {
            console.error('Error loading sessions:', error);
        }
    }

    render_sessions(sessions) {
        const $list = $('#session-list');
        $list.empty();

        if (sessions.length === 0) {
            $list.html('<div class="no-sessions">No active sessions. Click "New Chat" to start.</div>');
            return;
        }

        sessions.forEach(session => {
            const preview = session.first_message_preview || 'New conversation';
            const time = frappe.datetime.prettyDate(session.last_activity);

            const $item = $(`
                <div class="session-item ${session.session_id === this.session_id ? 'active' : ''}"
                     data-session-id="${session.session_id}">
                    <div class="session-preview">${frappe.utils.escape_html(preview)}</div>
                    <div class="session-meta">
                        <span class="session-time">${time}</span>
                        <span class="session-messages">${session.message_count} messages</span>
                    </div>
                </div>
            `);

            $item.on('click', () => this.select_session(session.session_id));
            $list.append($item);
        });
    }

    async create_session() {
        try {
            const response = await frappe.call({
                method: 'erpnext_chatbot.api.chat.create_session'
            });

            if (response.message && response.message.success) {
                this.session_id = response.message.message.session_id;
                this.enable_input();
                this.clear_messages();
                this.show_welcome();
                this.load_sessions();
                frappe.show_alert({ message: 'New chat session started', indicator: 'green' });
            } else {
                frappe.msgprint({ title: 'Error', message: response.message.error || 'Failed to create session', indicator: 'red' });
            }
        } catch (error) {
            console.error('Error creating session:', error);
            frappe.msgprint({ title: 'Error', message: 'Failed to create session', indicator: 'red' });
        }
    }

    async select_session(session_id) {
        this.session_id = session_id;
        this.enable_input();

        // Update active state in sidebar
        $('.session-item').removeClass('active');
        $(`.session-item[data-session-id="${session_id}"]`).addClass('active');

        // Load messages
        await this.load_messages();

        // Start polling
        this.start_polling();
    }

    async load_messages() {
        if (!this.session_id) return;

        try {
            const response = await frappe.call({
                method: 'erpnext_chatbot.api.chat.get_session_history',
                args: { session_id: this.session_id, limit: 50 }
            });

            if (response.message && response.message.success) {
                const messages = response.message.message.messages;
                this.clear_messages();

                if (messages.length === 0) {
                    this.show_welcome();
                } else {
                    this.hide_welcome();
                    messages.forEach(msg => this.append_message(msg.role, msg.content, msg.timestamp));

                    // Update last message time
                    if (messages.length > 0) {
                        this.last_message_time = messages[messages.length - 1].timestamp;
                    }
                }

                this.scroll_to_bottom();
            }
        } catch (error) {
            console.error('Error loading messages:', error);
        }
    }

    async poll_new_messages() {
        // Only poll if waiting for response
        if (!this.last_message_time) return;

        try {
            const response = await frappe.call({
                method: 'erpnext_chatbot.api.chat.get_new_messages',
                args: {
                    session_id: this.session_id,
                    after_timestamp: this.last_message_time
                }
            });

            if (response.message && response.message.success) {
                const messages = response.message.message.messages;
                messages.forEach(msg => {
                    this.append_message(msg.role, msg.content, msg.timestamp);
                    this.last_message_time = msg.timestamp;
                });

                if (messages.length > 0) {
                    this.scroll_to_bottom();
                }
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
    }

    async send_message() {
        const $input = $('#message-input');
        const message = $input.val().trim();

        if (!message || !this.session_id || this.is_waiting_response) {
            return;
        }

        // Clear input
        $input.val('');
        $input.css('height', 'auto');

        // Hide welcome message
        this.hide_welcome();

        // Show user message immediately
        this.append_message('user', message);
        this.scroll_to_bottom();

        // Show loading
        this.is_waiting_response = true;
        this.show_loading();

        try {
            const response = await frappe.call({
                method: 'erpnext_chatbot.api.chat.send_message',
                args: {
                    session_id: this.session_id,
                    message: message
                }
            });

            this.hide_loading();
            this.is_waiting_response = false;

            if (response.message && response.message.success) {
                const result = response.message.message;
                const chartData = result.chart || null;
                this.append_message('assistant', result.response, chartData);
                this.scroll_to_bottom();

                // Update rate limit display
                this.update_rate_limit();
            } else {
                const error = response.message.error || 'An error occurred';
                this.append_message('system', `Error: ${error}`);
                frappe.msgprint({ title: 'Error', message: error, indicator: 'red' });
            }
        } catch (error) {
            this.hide_loading();
            this.is_waiting_response = false;
            console.error('Error sending message:', error);
            this.append_message('system', 'Failed to send message. Please try again.');
        }
    }

    append_message(role, content, timestamp = null, chartData = null) {
        const $container = $('#chat-messages');
        const time = timestamp ? frappe.datetime.prettyDate(timestamp) : 'Just now';
        const messageId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);

        const roleClass = role === 'user' ? 'user-message' : (role === 'assistant' ? 'assistant-message' : 'system-message');
        const roleLabel = role === 'user' ? 'You' : (role === 'assistant' ? 'AI Assistant' : 'System');

        // Convert markdown-style formatting to HTML
        let formatted_content = frappe.utils.escape_html(content);
        formatted_content = this.format_message(formatted_content);

        // Create message HTML
        const $message = $(`
            <div class="chat-message ${roleClass}" id="${messageId}">
                <div class="message-header">
                    <span class="message-role">${roleLabel}</span>
                    <span class="message-time">${time}</span>
                </div>
                <div class="message-content">${formatted_content}</div>
                <div class="chart-container" id="${messageId}-chart" style="display: none;"></div>
            </div>
        `);

        $container.append($message);

        // Render chart if data is provided
        if (chartData && this.isValidChartData(chartData)) {
            this.render_chart(messageId, chartData);
        }
    }

    isValidChartData(chartData) {
        return (
            chartData &&
            chartData.chart_type &&
            ['bar', 'line', 'pie'].includes(chartData.chart_type) &&
            Array.isArray(chartData.labels) &&
            Array.isArray(chartData.values) &&
            chartData.labels.length >= 2 &&
            chartData.values.length >= 2
        );
    }

    render_chart(messageId, chartData) {
        const $chartContainer = $('#' + messageId + '-chart');

        if (!$chartContainer.length) {
            console.warn('Chart container not found:', messageId);
            return;
        }

        // Show chart container
        $chartContainer.show();

        // Add title if provided
        if (chartData.title) {
            $chartContainer.append('<div class="chart-title">' + frappe.utils.escape_html(chartData.title) + '</div>');
        }

        // Create canvas element
        const canvasId = messageId + '-canvas';
        $chartContainer.append('<canvas id="' + canvasId + '"></canvas>');

        // Wait for Chart.js to be available
        if (typeof Chart === 'undefined') {
            $chartContainer.html('<div class="chart-error">Chart library not loaded. Please refresh the page.</div>');
            return;
        }

        // Get chart configuration
        const config = this.get_chart_config(chartData);

        // Create chart instance
        try {
            const ctx = document.getElementById(canvasId).getContext('2d');
            this.charts[messageId] = new Chart(ctx, config);
        } catch (error) {
            console.error('Error rendering chart:', error);
            $chartContainer.html('<div class="chart-error">Failed to render chart.</div>');
        }
    }

    get_chart_config(chartData) {
        const chartType = chartData.chart_type;
        const labels = chartData.labels;
        const values = chartData.values;
        const colors = chartData.colors || [
            '#2491eb', '#5e64ff', '#00c3b3', '#28c76f', '#ff6b6b',
            '#f9c846', '#743ee2', '#ea5455', '#a5a5a5', '#1a1a2e'
        ];

        const config = {
            type: chartType,
            data: {
                labels: labels,
                datasets: [{
                    label: chartData.title || 'Value',
                    data: values,
                    backgroundColor: chartType === 'pie' ? colors : colors[0],
                    borderColor: chartType === 'line' ? colors[0] : '#fff',
                    borderWidth: 2,
                    fill: chartType === 'line',
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: chartType === 'pie',
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null || context.parsed !== null) {
                                    // Format as currency if values are large
                                    const val = context.parsed;
                                    if (val > 1000) {
                                        label += '$' + val.toLocaleString('en-US', { maximumFractionDigits: 0 });
                                    } else {
                                        label += val.toLocaleString();
                                    }
                                }
                                return label;
                            }
                        }
                    }
                },
                animation: {
                    duration: 500
                }
            }
        };

        // Add scales for bar and line charts
        if (chartType === 'bar' || chartType === 'line') {
            config.options.scales = {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#f0f0f0'
                    },
                    ticks: {
                        callback: function(value) {
                            if (value >= 1000000) {
                                return '$' + (value / 1000000).toFixed(1) + 'M';
                            } else if (value >= 1000) {
                                return '$' + (value / 1000).toFixed(0) + 'K';
                            }
                            return value;
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            };
        }

        // For pie charts, show percentages
        if (chartType === 'pie') {
            const total = values.reduce((a, b) => a + b, 0);
            config.options.plugins.tooltip.callbackes = {
                label: function(context) {
                    const value = context.parsed;
                    const percentage = ((value / total) * 100).toFixed(1);
                    return context.label + ': ' + percentage + '% (' + value.toLocaleString() + ')';
                }
            };
        }

        return config;
    }

    destroy_chart(messageId) {
        if (this.charts[messageId]) {
            try {
                this.charts[messageId].destroy();
            } catch (error) {
                console.warn('Error destroying chart:', error);
            }
            delete this.charts[messageId];
        }
    }

    format_message(text) {
        // Convert **bold** to <strong>
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Convert line breaks
        text = text.replace(/\n/g, '<br>');

        // Convert markdown tables to HTML
        text = this.convert_tables(text);

        // Convert bullet points
        text = text.replace(/^- (.*)$/gm, '<li>$1</li>');
        text = text.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');

        return text;
    }

    convert_tables(text) {
        // Simple markdown table detection and conversion
        const tableRegex = /\|(.+)\|[\r\n]+\|[-|]+\|[\r\n]+((?:\|.+\|[\r\n]*)+)/g;

        return text.replace(tableRegex, (match, header, body) => {
            const headers = header.split('|').filter(h => h.trim());
            const rows = body.trim().split('\n').map(row =>
                row.split('|').filter(cell => cell.trim())
            );

            let html = '<table class="table table-bordered table-sm"><thead><tr>';
            headers.forEach(h => html += `<th>${h.trim()}</th>`);
            html += '</tr></thead><tbody>';
            rows.forEach(row => {
                html += '<tr>';
                row.forEach(cell => html += `<td>${cell.trim()}</td>`);
                html += '</tr>';
            });
            html += '</tbody></table>';

            return html;
        });
    }

    clear_messages() {
        $('#chat-messages .chat-message').remove();
    }

    show_welcome() {
        $('#welcome-message').show();
    }

    hide_welcome() {
        $('#welcome-message').hide();
    }

    show_loading() {
        $('#loading-overlay').show();
        $('#send-btn').prop('disabled', true);
    }

    hide_loading() {
        $('#loading-overlay').hide();
        $('#send-btn').prop('disabled', false);
    }

    enable_input() {
        $('#message-input').prop('disabled', false);
        $('#send-btn').prop('disabled', false);
    }

    disable_input() {
        $('#message-input').prop('disabled', true);
        $('#send-btn').prop('disabled', true);
    }

    scroll_to_bottom() {
        const $container = $('#chat-messages');
        $container.scrollTop($container[0].scrollHeight);
    }

    start_polling() {
        // Stop existing polling
        this.stop_polling();

        // Start new polling interval (every 3 seconds)
        this.poll_interval = setInterval(() => {
            if (!this.is_waiting_response && this.session_id) {
                this.poll_new_messages();
            }
        }, 3000);
    }

    stop_polling() {
        if (this.poll_interval) {
            clearInterval(this.poll_interval);
            this.poll_interval = null;
        }
    }

    async close_session() {
        if (!this.session_id) return;

        frappe.confirm(
            'Are you sure you want to close this chat session?',
            async () => {
                try {
                    const response = await frappe.call({
                        method: 'erpnext_chatbot.api.chat.close_session',
                        args: { session_id: this.session_id }
                    });

                    if (response.message && response.message.success) {
                        frappe.show_alert({ message: 'Session closed', indicator: 'green' });
                        this.session_id = null;
                        this.stop_polling();
                        this.clear_messages();
                        this.show_welcome();
                        this.disable_input();
                        this.load_sessions();
                    }
                } catch (error) {
                    console.error('Error closing session:', error);
                }
            }
        );
    }

    async update_rate_limit() {
        try {
            const response = await frappe.call({
                method: 'erpnext_chatbot.api.chat.get_rate_limit_status'
            });

            if (response.message && response.message.success) {
                const status = response.message.message;
                $('#rate-limit-status').text(`${status.remaining}/${status.limit} requests remaining`);
            }
        } catch (error) {
            // Ignore rate limit status errors
        }
    }
}
