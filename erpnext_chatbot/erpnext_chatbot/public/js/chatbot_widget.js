// ERPNext Chatbot Widget
// This file is included globally and provides quick access to chatbot

frappe.provide('erpnext_chatbot');

erpnext_chatbot.show_chatbot = function() {
    frappe.set_route('chatbot');
};

// Add chatbot button to navbar (optional)
$(document).ready(function() {
    // This can be enabled to add a floating chatbot button
    // Uncomment if needed

    /*
    if (frappe.session.user !== 'Guest') {
        $('body').append(`
            <div id="chatbot-fab" style="
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 56px;
                height: 56px;
                border-radius: 50%;
                background: #2196f3;
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                z-index: 1000;
                transition: transform 0.2s;
            ">
                <i class="fa fa-comments fa-lg"></i>
            </div>
        `);

        $('#chatbot-fab').on('click', function() {
            erpnext_chatbot.show_chatbot();
        });

        $('#chatbot-fab').on('mouseenter', function() {
            $(this).css('transform', 'scale(1.1)');
        });

        $('#chatbot-fab').on('mouseleave', function() {
            $(this).css('transform', 'scale(1)');
        });
    }
    */
});
