if (!$) {
    $ = django.jQuery;

    $(document).ready(function() {
        text_template = document.getElementById('id_text_template');
        if (text_template) {
            var textEditor = CodeMirror.fromTextArea(text_template, {
                'mode': 'django',
                'theme': 'monokai',
                'lineNumbers': true,
                'lineWrapping': true,
                'indentUnit': 2,
                'indentWithTabs': false,
            });
        }

        html_template = document.getElementById('id_html_template');
        if (html_template) {
            var htmlEditor = CodeMirror.fromTextArea(html_template, {
                'mode': 'django',
                'theme': 'monokai',
                'lineNumbers': true,
                'lineWrapping': true,
                'indentUnit': 2,
                'indentWithTabs': false,
            });

            var panel = document.createElement('div');
            panel.className = 'codemirror-panel top'

            // Code tab
            var code = panel.appendChild(document.createElement('a'));
            code.textContent = 'Code';
            CodeMirror.on(code, 'click', function() {
                $('.field-html_template .CodeMirror').show();
                $('#codemirror-preview').hide();
            });

            // Preview tab
            var preview = panel.appendChild(document.createElement('a'));
            preview.textContent = 'Preview';

            // Create preview iFrame
            $('.field-html_template > div label').after($('<iframe>', {
                id: 'codemirror-preview',
                css: {
                    display: 'none'
                }
            }));

            CodeMirror.on(preview, 'click', function() {
                $('.field-html_template .CodeMirror').hide();

                // Update preview
                var previewFrame = document.getElementById('codemirror-preview');
                var preview =  previewFrame.contentDocument ||  previewFrame.contentWindow.document;
                preview.open();
                preview.write(htmlEditor.getValue());
                preview.close();

                $('#codemirror-preview').show();
            });

            // Fullscreen
            /*var fullscreen = panel.appendChild(document.createElement('a'));
            fullscreen.textContent = 'Fullscreen';
            CodeMirror.on(fullscreen, 'click', function() {
                alert('full')
            });*/

            // Attach panel
            htmlEditor.addPanel(panel, {
                position: 'bottom',
                stable: false
            });
        }
    });
}
