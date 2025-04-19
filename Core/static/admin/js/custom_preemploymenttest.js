// custom_preemploymenttest.js
(function($) {
    $(document).ready(function() {
        $('#id_applicant').change(function() {
            var applicantId = $(this).val();
            if (applicantId) {
                var url = '/admin/get_applicant_job_openings/?applicant_id=' + applicantId;
                $.ajax({
                    url: url,
                    success: function(data) {
                        var $jobOpeningSelect = $('#id_job_opening');
                        $jobOpeningSelect.html('');
                        $.each(data, function(index, item) {
                            $jobOpeningSelect.append($('<option>', {
                                value: item.id,
                                text: item.title
                            }));
                        });
                    }
                });
            } else {
                $('#id_job_opening').html('');
            }
        });
    });
})(django.jQuery);