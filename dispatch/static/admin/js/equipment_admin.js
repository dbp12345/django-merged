(function($) {
    'use strict';

    $(document).ready(function() {
        var equipmentTypeField = $('#id_equipment_type');
        var parametersField = $('#id_parameters');
        var parametersRow = parametersField.closest('.form-row');
        var equipmentId = null;

        // Get equipment ID from URL if editing
        var urlMatch = window.location.pathname.match(/\/dispatch\/equipment\/(\d+)\/change\//);
        if (urlMatch) {
            equipmentId = urlMatch[1];
        }

        if (!equipmentTypeField.length || !parametersField.length) {
            return; // Not on equipment form
        }

        var currentEquipmentTypeId = equipmentTypeField.val();

        // Create message container
        var messageHtml = '<div class="form-row" style="background: #fff3cd; padding: 10px; margin: 10px 0; border: 1px solid #ffc107; display: none;" id="schema-change-message">' +
            '<p class="help" style="margin: 0;"><strong>Schema updated:</strong> Please save the form to see the updated parameter fields for the selected equipment type.</p>' +
            '</div>';
        var messageContainer = $(messageHtml);
        parametersRow.after(messageContainer);

        // Function to handle type change
        equipmentTypeField.on('change', function() {
            var newTypeId = $(this).val();

            if (!newTypeId) {
                // Clear if no type selected
                parametersField.val('{}');
                currentEquipmentTypeId = null;
                messageContainer.hide();
                return;
            }

            if (newTypeId === currentEquipmentTypeId) {
                return; // Type hasn't changed
            }

            // Build URL for schema
            var url = '/admin/equipment/type/' + newTypeId + '/schema/';
            if (equipmentId) {
                url += '?equipment_id=' + equipmentId;
            }

            // Fetch new schema
            $.ajax({
                url: url,
                method: 'GET',
                success: function(response) {
                    if (response.status === 'success' && response.schema) {
                        // Filter parameters to keep only keys from new schema
                        var currentParams = {};
                        if (parametersField.val()) {
                            try {
                                currentParams = JSON.parse(parametersField.val());
                            } catch (e) {
                                currentParams = {};
                            }
                        }

                        var schemaKeys = Object.keys(response.schema.keys || {});
                        var filteredParams = {};

                        // Keep only keys that exist in new schema
                        for (var key in currentParams) {
                            if (schemaKeys.indexOf(key) !== -1) {
                                filteredParams[key] = currentParams[key];
                            }
                        }

                        // Update field value
                        parametersField.val(JSON.stringify(filteredParams));

                        // Update current type
                        currentEquipmentTypeId = newTypeId;

                        // Show message
                        messageContainer.show();
                    } else {
                        console.error('Invalid response:', response);
                    }
                },
                error: function(xhr, status, error) {
                    console.error('Error loading schema:', error);
                    alert('Error loading schema. Please try again.');
                }
            });
        });

        // Hide message when form is submitted
        $('form').on('submit', function() {
            messageContainer.hide();
        });
    });
})(django.jQuery || jQuery);
