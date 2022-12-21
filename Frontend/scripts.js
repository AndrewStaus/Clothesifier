function readURL(input) {
    if (input.files && input.files[0]) {
      var reader = new FileReader();
  
      reader.onload = function (e) {
        $('#fileDisplay').show().attr('src', e.target.result);
      };
      document.getElementById('fileName').innerText = input.files[0].name
      reader.readAsDataURL(input.files[0]);
    }
}

function updateTable(object){
  var table = document.getElementById("table");
  $("#table").find("tr:not(:first)").remove();

  var count = 1
  for(property in object){
    var row = table.insertRow();
    var pos = row.insertCell(0);
    var name = row.insertCell(1);
    var conf = row.insertCell(2);

    pos.innerHTML = count++;
    name.innerHTML = `${object[property].name}`;
    conf.innerHTML = `${object[property].conf}%`;
  }
}



async function uploadFile() {
    var $alert = $('.alert');
    let formData = new FormData();
    var reader = new FileReader();
    reader.onload = function (readerEvent){
      var image = new Image();
      image.onload = function (imageEvent){
        var canvas = document.createElement('canvas'),
          max_size = 28,
          width = image.width,
          height = image.height;
          if (width > height) {
            if (width > max_size) {
                height *= max_size / width;
                width = max_size;
            }
          } else {
              if (height > max_size) {
                  width *= max_size / height;
                  height = max_size;
              }
          }
          canvas.width = width;
          canvas.height = height;
          canvas.getContext('2d').drawImage(image, 0, 0, width, height);
          var dataUrl = canvas.toDataURL('image/jpeg');
          var resizedImage = dataURLToBlob(dataUrl);
          formData.append("file", resizedImage);
          $.ajax('https://xxlkbgor75nvr7qw256z2xnrdm0ppqai.lambda-url.us-east-2.on.aws/image', {
              method: 'POST',
              data: formData,
              processData: false,
              contentType: false,
                      
              success: function (data) {
                  $alert.hide();
                  document.getElementById('result').innerHTML = data.category
                  updateTable(data.confs)
                  },
              error: function () {
                  $alert.show();
                  }
          });
      }
    }
}