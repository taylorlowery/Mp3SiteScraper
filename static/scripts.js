$("#button-single-file").click(function(){
    jsonData = {
        "file_id": $("#single-file-id").val(),
        "metadata_only": false,
        "redownload": $("#cb-redownload-file").is(":checked")
    };
   $.ajax({
      url: "/singlefile",
       type: "post",
       data: JSON.stringify(jsonData),
       dataType: 'json',
       contentType: "application/json",
       success: function(response){
           console.log(response);
           $("#single-file-response").html(response)
       },
       error: function(xhr) {
          console.log(xhr);
          $("#single-file-response").html(xhr)
       }
   });
});
$("#button-file-range").click(function(){
    jsonData = {
          "first_file_id": $("#file-range-first-id").val(),
           "last_file_id": $("#file-range-last-id").val(),
            "metadata_only": false,
            "redownload": $("#cb-redownload-range").is(":checked")
       };
   $.ajax({
      url: "/filerange",
       type: "post",
       data: JSON.stringify(jsonData),
       dataType: 'json',
       contentType: "application/json",
       success: function(response){
          console.log(response);
          $("#file-range-response").html(response)
       },
       error: function(xhr) {
          console.log(xhr);
          $("#file-range-response").html(xhr)
       }
   });
});
$("#button-all-files").click(function(){
   $.ajax({
      url: "/allfiles",
       type: "post",
       data: {"test": "all-file"},
       contentType: "application/json",
       success: function(response){
          console.log(response);
          $("#all-files-response").html(response)
       },
       error: function(xhr) {
          console.log(xhr);
          $("#all-files-response").html(xhr)
       }
   });
});
$("#button-single-file-metadata").click(function(){
    jsonData = {
        "file_id": $("#single-file-id").val(),
            "metadata_only": $("#cb-redownload-file").is(":checked")
    };
   $.ajax({
      url: "/singlefile",
       type: "post",
       data: JSON.stringify(jsonData),
       dataType: 'json',
       contentType: "application/json",
       success: function(response){
           console.log(response);
           $("#single-file-response").html(response)
       },
       error: function(xhr) {
          console.log(xhr);
          $("#single-file-response").html(xhr)
       }
   });
});
$("#button-file-range-metadata").click(function(){
    jsonData = {
          "first_file_id": $("#file-range-first-id").val(),
           "last_file_id": $("#file-range-last-id").val(),
            "metadata_only": true
       };
   $.ajax({
      url: "/filerange",
       type: "post",
       data: JSON.stringify(jsonData),
       dataType: 'json',
       contentType: "application/json",
       success: function(response){
          console.log(response);
          $("#file-range-response").html(response)
       },
       error: function(xhr) {
          console.log(xhr);
          $("#file-range-response").html(xhr)
       }
   });
});
$("#button-all-files-metadata").click(function(){
   $.ajax({
      url: "/allmetadata",
       type: "post",
       data: {"test": "all-file"},
       contentType: "application/json",
       success: function(response){
          console.log(response);
          $("#all-files-response").html(response)
       },
       error: function(xhr) {
          console.log(xhr);
          $("#all-files-response").html(xhr)
       }
   });
});