/* global define, jQuery */
(function (factory) {
  if (typeof define === 'function' && define.amd) {
    define(['jquery'], factory)
  } else if (typeof module === 'object' && module.exports) {
    module.exports = factory(require('jquery'))
  } else {
    // Browser globals
    factory(jQuery || django.jQuery)
  }
}(function ($) {
  'use strict'

  let init = function ($element, options) {
    $element.select2(options)
  }

  let initHeavy = function ($element, options) {
    var settings = $.extend({
      ajax: {
        data: function (params) {
          var result = {
            term: params.term,
            page: params.page,
            field_id: $element.data('field_id')
          }

          var dependentFields = $element.data('select2-dependent-fields')
          if (dependentFields) {
            dependentFields = dependentFields.trim().split(/\s+/)
            $.each(dependentFields, function (i, dependentField) {
              // result[dependentField] = $('[name=' + dependentField + ']', $element.closest('form')).val()
              // Hook InlineFormSet
              var formValue = $('[name=' + dependentField + ']', $element.closest('form')).val();
              // This is for inline, I checked this for a specific case
              if (formValue === null || formValue === undefined) {
                var newFieldName = $element[0].name.split('-', 2).join('-') + '-' + dependentField;
                formValue = $('[name=' + newFieldName + ']', $element.closest('.form-row')).val();
                // Hook Change list formset (*_|*)
                if (formValue === null || formValue === undefined){
                  formValue = $('[name=' + newFieldName + ']', $element.closest('tr')).val();
                }
              }
              result[dependentField] = formValue;
            })
          }

          return result
        },
        processResults: function (data, page) {
          return {
            results: data.results,
            pagination: {
              more: data.more
            }
          }
        }
      }
    }, options)

    return $element.select2(settings)
  }

  let resetSelectedItem = function (e) {

    let name = $(e.currentTarget).attr('name')


    $("[data-select2-dependent-fields~='" + name + "']").each(function () {
      $(this).val(null).trigger('change');
    })
    // Hook InlineFormset
    let inline_name = name.trim().split('-', -1).reverse()[0]
    if (inline_name != name) {
      $("[data-select2-dependent-fields~='" + inline_name + "']", $(e.currentTarget).closest('.form-row')).each(function () {
        // if($(this).data("allow-clear"))
          $(this).val(null).trigger('change');
      })
      // Hook change list formset
      $("[data-select2-dependent-fields~='" + inline_name + "']", $(e.currentTarget).closest('tr')).each(function () {
        $(this).val(null).trigger('change');
      })
    }

  }
  $.fn.djangoSelect2 = function (options) {
    let settings = $.extend({}, options)
    $.each(this, function (i, element) {
      let $element = $(element)
      if ($element.hasClass('django-select2-heavy')) {
        initHeavy($element, settings)
      } else {
        init($element, settings)
      }
      $element.on('select2:select', function (e) {
        resetSelectedItem(e)
      });
      $element.on('select2:clear', function (e) {
        resetSelectedItem(e)
      });
      $element.on('select2:unselect', function (e) {
        resetSelectedItem(e)
      });
    })
    return this
  }

  $.fn.hookDjangoAdminAutocomplete = function (options) {
    let settings = $.extend({}, options)
    $.each(this, function (i, element) {
      let $element = $(element);
      $element.on('select2:select', function (e) {
        resetSelectedItem(e)
      });
      $element.on('select2:clear', function (e) {
        resetSelectedItem(e)
      });
      $element.on('select2:unselect', function (e) {
        resetSelectedItem(e)
      });
    });
    return this
  }

  $(function () {
    // Initialize all autocomplete widgets except the one in the template
    // form used when a new formset is added.
    // deprecationInit()
    // $('.django-select2').djangoSelect2()
    $('.django-select2').not('[name*=__prefix__]').djangoSelect2();

    // Hook django admin autocomplete
    $('.admin-autocomplete').not('[name*=__prefix__]').hookDjangoAdminAutocomplete()

  });
  document.addEventListener('formset:added', (event) => {
    $(event.target).find('.django-select2').djangoSelect2();
  });

  // return $.fn.djangoSelect2
}));

/*
  function initDjangoSelect2(element) {
    if (element.classList.contains('django-select2')) {
      $(element).djangoSelect2();
    } else {
      element.querySelectorAll('.django-select2').forEach(djSelect => {
        if (djSelect.closest('.empty-form') === null) {
          $(djSelect).djangoSelect2();
        }
      });
    }
  }
  function deprecationInit() {
    document.querySelectorAll('.django-select2').forEach(element => {
      if (element.closest('.empty-form') === null) {
        $(element).djangoSelect2();
      }
    });
    $(document).on('formset:added', (event, $row, formsetName) => {
      if (event.detail && event.detail.formsetName) {
        // Django >= 4.1
        initDjangoSelect2(event.target);
      } else {
        // Django < 4.1, use $row
        initDjangoSelect2($row.get(0));
      }
    });
  }
*/